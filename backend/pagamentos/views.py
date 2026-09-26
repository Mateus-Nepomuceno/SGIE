import logging
from decimal import Decimal
from typing import override

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from eventos.models import Evento
from pagamentos.models import (
    CategoriaPreco,
    Certificado,
    Cobranca,
    Lote,
    Pagamento,
    Reembolso,
    StatusCobranca,
    StatusPagamento,
    StatusReembolso,
)
from pagamentos.permissions import (
    IsDonoDoObjetoOuOrganizador,
    IsOrganizadorDoEventoOuAdmin,
    usuario_e_organizador_ou_admin,
)
from pagamentos.serializers import (
    CategoriaPrecoSerializer,
    CertificadoSerializer,
    CobrancaSerializer,
    ConcederIsencaoInputSerializer,
    CriarCobrancaInputSerializer,
    LoteSerializer,
    PagamentoSerializer,
    ProcessarPagamentoInputSerializer,
    ReembolsoSerializer,
    SolicitarReembolsoInputSerializer,
    WebhookPagamentoSerializer,
)
from pagamentos.services import ServicoCobranca, ServicoPagamento
from usuarios.models import Papel

logger = logging.getLogger(__name__)


def get_eventos_organizados_ids(user) -> list[int]:
    """Retorna a lista de IDs de eventos onde o usuário atua como organizador."""
    if not user or not user.is_authenticated:
        return []
    return list(user.papeis_contextuais.filter(papel=Papel.ORGANIZADOR, ativo=True).values_list('evento_id', flat=True))


class CategoriaPrecoViewSet(viewsets.ModelViewSet):
    """
    CRUD de categorias de preço do evento (UC2).
    Apenas organizadores do evento ou administradores podem criar ou alterar.
    """

    queryset = CategoriaPreco.objects.select_related('evento').all()
    serializer_class = CategoriaPrecoSerializer
    permission_classes = [IsOrganizadorDoEventoOuAdmin]

    @override
    def get_queryset(self):
        queryset = super().get_queryset()
        evento_id = self.request.query_params.get('evento')
        if evento_id:
            queryset = queryset.filter(evento_id=evento_id)
        return queryset


class LoteViewSet(viewsets.ModelViewSet):
    """
    CRUD de lotes e vagas para categorias de preço (UC2).
    Apenas organizadores do evento ou administradores podem criar ou alterar.
    """

    queryset = Lote.objects.select_related('categoria_preco__evento').all()
    serializer_class = LoteSerializer
    permission_classes = [IsOrganizadorDoEventoOuAdmin]

    @override
    def get_queryset(self):
        queryset = super().get_queryset()
        categoria_id = self.request.query_params.get('categoria')
        evento_id = self.request.query_params.get('evento')
        if categoria_id:
            queryset = queryset.filter(categoria_preco_id=categoria_id)
        if evento_id:
            queryset = queryset.filter(categoria_preco__evento_id=evento_id)
        return queryset


class CobrancaViewSet(viewsets.ModelViewSet):
    """
    Gestão de Cobranças (UC12, UC8, UC4).
    Participantes visualizam suas cobranças e podem realizar o pagamento.
    Organizadores podem emitir cobranças e conceder isenções.
    """

    serializer_class = CobrancaSerializer
    permission_classes = [IsDonoDoObjetoOuOrganizador]

    @override
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Cobranca.objects.none()

        if user.is_staff or user.is_superuser:
            return Cobranca.objects.select_related('inscricao__evento', 'inscricao__usuario', 'lote', 'isencao').all()

        org_eventos_ids = get_eventos_organizados_ids(user)
        return Cobranca.objects.filter(Q(inscricao__usuario=user) | Q(inscricao__evento__usuario_representante=user) | Q(inscricao__evento_id__in=org_eventos_ids)).distinct().select_related('inscricao__evento', 'inscricao__usuario', 'lote', 'isencao')

    @override
    def create(self, request, *args, **kwargs):
        """Emite uma nova cobrança para uma inscrição (UC12)."""
        serializer = CriarCobrancaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inscricao = serializer.validated_data['inscricao']
        lote = serializer.validated_data.get('lote')
        categoria = serializer.validated_data.get('categoria')
        dias_vencimento = serializer.validated_data.get('dias_vencimento', 3)

        # Validação de permissão: participante pode gerar para si mesmo, organizador para o evento
        if inscricao.usuario_id != request.user.id and not usuario_e_organizador_ou_admin(request.user, inscricao.evento):
            raise PermissionDenied('Você não possui autorização para gerar cobrança para esta inscrição.')

        try:
            cobranca = ServicoCobranca.gerar_cobranca(
                inscricao=inscricao,
                categoria=categoria,
                lote=lote,
                dias_vencimento=dias_vencimento,
            )
        except DjangoValidationError as e:
            raise ValidationError(e.message if hasattr(e, 'message') else str(e))

        output_serializer = CobrancaSerializer(cobranca)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='pagar')
    def pagar(self, request, pk=None):
        """
        Realiza o pagamento de uma cobrança gerando a transação no gateway (UC8, UC7).
        """
        cobranca = self.get_object()
        serializer = ProcessarPagamentoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        metodo = serializer.validated_data['metodo']
        dados_cartao = serializer.validated_data.get('dados_cartao', {})
        retorno_url = serializer.validated_data.get('retorno_url', '')

        servico = ServicoPagamento()
        try:
            pagamento = servico.processar_pagamento(
                cobranca=cobranca,
                metodo_pagamento=metodo,
                dados_cartao=dados_cartao,
                retorno_url=retorno_url,
            )
        except DjangoValidationError as e:
            raise ValidationError(e.message if hasattr(e, 'message') else str(e))

        output_serializer = PagamentoSerializer(pagamento)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        url_path='conceder-isencao',
        permission_classes=[permissions.IsAuthenticated],
    )
    def conceder_isencao(self, request, pk=None):
        """
        Concede isenção total ou abatimento parcial em uma cobrança pendente (UC4).
        Exclusivo para organizadores do evento ou administradores.
        """
        cobranca = self.get_object()
        if not usuario_e_organizador_ou_admin(request.user, cobranca.inscricao.evento):
            raise PermissionDenied('Apenas o organizador do evento pode conceder isenções.')

        serializer = ConcederIsencaoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tipo = serializer.validated_data['tipo']
        motivo = serializer.validated_data['motivo']
        desconto_percentual = serializer.validated_data.get('desconto_percentual')
        desconto_valor = serializer.validated_data.get('desconto_valor')

        try:
            ServicoCobranca.conceder_isencao(
                cobranca=cobranca,
                tipo=tipo,
                motivo=motivo,
                aprovado_por=request.user,
                desconto_percentual=desconto_percentual,
                desconto_valor=desconto_valor,
            )
        except DjangoValidationError as e:
            raise ValidationError(e.message if hasattr(e, 'message') else str(e))

        cobranca.refresh_from_db()
        return Response(CobrancaSerializer(cobranca).data, status=status.HTTP_200_OK)


class PagamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consulta de transações de pagamento e solicitação de reembolso (UC9, UC10).
    """

    serializer_class = PagamentoSerializer
    permission_classes = [IsDonoDoObjetoOuOrganizador]

    @override
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Pagamento.objects.none()

        if user.is_staff or user.is_superuser:
            return Pagamento.objects.select_related('cobranca__inscricao').all()

        org_eventos_ids = get_eventos_organizados_ids(user)
        return Pagamento.objects.filter(Q(cobranca__inscricao__usuario=user) | Q(cobranca__inscricao__evento__usuario_representante=user) | Q(cobranca__inscricao__evento_id__in=org_eventos_ids)).distinct().select_related('cobranca__inscricao')

    @action(detail=True, methods=['post'], url_path='solicitar-reembolso')
    def solicitar_reembolso(self, request, pk=None):
        """
        Solicita e processa o reembolso de um pagamento aprovado (UC10, UC13).
        """
        pagamento = self.get_object()
        serializer = SolicitarReembolsoInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        motivo = serializer.validated_data['motivo']
        valor = serializer.validated_data.get('valor')

        servico = ServicoPagamento()
        try:
            reembolso = servico.solicitar_reembolso(
                pagamento=pagamento,
                motivo=motivo,
                solicitado_por=request.user,
                valor=valor,
            )
        except DjangoValidationError as e:
            raise ValidationError(e.message if hasattr(e, 'message') else str(e))

        output_serializer = ReembolsoSerializer(reembolso)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class ReembolsoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consulta de processos de reembolso (UC13).
    """

    serializer_class = ReembolsoSerializer
    permission_classes = [IsDonoDoObjetoOuOrganizador]

    @override
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Reembolso.objects.none()

        if user.is_staff or user.is_superuser:
            return Reembolso.objects.select_related('pagamento__cobranca__inscricao').all()

        org_eventos_ids = get_eventos_organizados_ids(user)
        return Reembolso.objects.filter(Q(solicitado_por=user) | Q(pagamento__cobranca__inscricao__evento__usuario_representante=user) | Q(pagamento__cobranca__inscricao__evento_id__in=org_eventos_ids)).distinct().select_related('pagamento__cobranca__inscricao')


class CertificadoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consulta e validação de certificados (UC11, UC5).
    """

    serializer_class = CertificadoSerializer
    permission_classes = [IsDonoDoObjetoOuOrganizador]

    @override
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Certificado.objects.none()

        if user.is_staff or user.is_superuser:
            return Certificado.objects.select_related('inscricao__evento', 'inscricao__usuario').all()

        org_eventos_ids = get_eventos_organizados_ids(user)
        return Certificado.objects.filter((Q(inscricao__usuario=user) & Q(disponivel=True)) | Q(inscricao__evento__usuario_representante=user) | Q(inscricao__evento_id__in=org_eventos_ids)).distinct().select_related('inscricao__evento', 'inscricao__usuario')

    @action(
        detail=False,
        methods=['get'],
        url_path='validar/(?P<codigo>[^/.]+)',
        permission_classes=[permissions.AllowAny],
    )
    def validar(self, request, codigo=None):
        """
        Validação pública de autenticidade de um certificado via código hash.
        """
        _ = self.request
        certificado = get_object_or_404(
            Certificado.objects.select_related('inscricao__evento', 'inscricao__usuario'),
            codigo_autenticacao=codigo,
            disponivel=True,
        )
        return Response({
            'autentico': True,
            'codigo': certificado.codigo_autenticacao,
            'evento': certificado.inscricao.evento.nome,
            'participante': certificado.inscricao.usuario.nome_completo,
            'carga_horaria': certificado.carga_horaria,
            'emitido_em': certificado.emitido_em,
        })


class WebhookPagamentoView(APIView):
    """
    Endpoint para recepção de webhooks do Gateway/PSP.
    """

    permission_classes = [permissions.AllowAny]

    @override
    def post(self, request, *args, **kwargs):
        serializer = WebhookPagamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transacao_id = serializer.validated_data['transacao_id']
        status_pagamento = serializer.validated_data['status']
        detalhes = serializer.validated_data.get('detalhes', {})

        try:
            pagamento = ServicoPagamento.processar_notificacao_webhook(
                transacao_id=transacao_id,
                novo_status=status_pagamento,
                detalhes=detalhes,
            )
        except DjangoValidationError as e:
            return Response({'erro': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'status': 'processado',
                'transacao_id': pagamento.transacao_id,
                'pagamento_status': pagamento.status,
            },
            status=status.HTTP_200_OK,
        )


class RelatorioFinanceiroEventoView(APIView):
    """
    Geração de relatório e métricas financeiras do evento (UC3).
    Apenas organizadores ou administradores.
    """

    permission_classes = [permissions.IsAuthenticated]

    @override
    def get(self, request, evento_id: int):
        evento = get_object_or_404(Evento, pk=evento_id)
        if not usuario_e_organizador_ou_admin(request.user, evento):
            raise PermissionDenied('Apenas o organizador do evento pode acessar relatórios financeiros.')

        cobrancas = Cobranca.objects.filter(inscricao__evento=evento)
        pagamentos = Pagamento.objects.filter(cobranca__inscricao__evento=evento)
        reembolsos = Reembolso.objects.filter(pagamento__cobranca__inscricao__evento=evento)

        total_arrecadado = pagamentos.filter(status=StatusPagamento.APROVADO).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        total_pendente = cobrancas.filter(status=StatusCobranca.PENDENTE).aggregate(total=Sum('valor_final'))['total'] or Decimal('0.00')

        total_reembolsado = reembolsos.filter(status=StatusReembolso.CONCLUIDO).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        total_liquido = total_arrecadado - total_reembolsado

        distribuicao_metodos = list(pagamentos.filter(status=StatusPagamento.APROVADO).values('metodo').annotate(quantidade=Count('id'), total=Sum('valor')))

        vendas_por_lote = list(cobrancas.filter(status=StatusCobranca.PAGA, lote__isnull=False).values('lote__nome', 'lote__numero').annotate(quantidade=Count('id'), total=Sum('valor_final')))

        return Response({
            'evento_id': evento.id,
            'evento_nome': evento.nome,
            'total_arrecadado_bruto': total_arrecadado,
            'total_reembolsado': total_reembolsado,
            'total_liquido': total_liquido,
            'total_pendente': total_pendente,
            'total_cobrancas': cobrancas.count(),
            'distribuicao_metodos': distribuicao_metodos,
            'vendas_por_lote': vendas_por_lote,
        })

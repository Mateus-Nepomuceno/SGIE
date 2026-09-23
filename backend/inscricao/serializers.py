from rest_framework import serializers
from .models import Inscricao

class InscricaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscricao
        fields = ['id', 'evento', 'comprovante', 'dados_adicionais', 'status']
        read_only_fields = ['status', 'id']

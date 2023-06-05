from rest_framework import serializers

from api.models import Loan, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'email',
            'id',
            'lastmod',
        )


class UserLoanSerializer(serializers.ModelSerializer):
    customer = serializers.UUIDField(
        source='customer_id',
    )
    amount = serializers.IntegerField()
    term = serializers.IntegerField()
    repay_details = serializers.JSONField()

    class Meta:
        model = Loan
        fields = (
            'customer',
            'id',
            'amount',
            'term',
            'date',
            'repay_details',
            'status',
            'lastmod',
        )

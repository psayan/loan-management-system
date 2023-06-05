from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.lms_exceptions import BadRequest, Conflict
from api.models import Loan, UserProfile
from api.userprofile.serializers import UserLoanSerializer, UserSerializer
from api.utils import today


class MasterUserList(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        master_user = request.data
        email = master_user.get('email')
        password = master_user.get('password')
        if not email or not password:
            raise BadRequest('Required fields are missing! Those are email and password.')

        user_exists = UserProfile.objects.filter(
            email=email
        ).exists()
        if user_exists:
            raise Conflict(
                f'User exists with email {email}.'
            )
        (auth_user, is_auth_user_created) = User.objects.get_or_create(
            username=email,
            password=password,
        )
        Token.objects.get_or_create(user=auth_user)
        master_user['lastmod'] = today()
        with transaction.atomic():
            user_serializer = UserSerializer(data=master_user)
            if user_serializer.is_valid(raise_exception=True):
                user = user_serializer.save()
                user.user = auth_user
                user.save()
        response_data = user_serializer.data
        response_data['is_admin'] = request.user.is_superuser
        return Response(response_data)

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")
        users = UserProfile.objects.all()
        master_users = UserSerializer(
            users,
            context={'request': request},
            many=True,
        ).data
        modified_master_users = []
        for master_user in master_users:
            user = User.objects.get(username=master_user['email'])
            master_user['is_admin'] = user.is_superuser
            modified_master_users.append(master_user)
        return Response(modified_master_users)


class MasterUserToken(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get('email')
        if not email:
            raise BadRequest('The field email is mandatory to get token!')
        try:
            user = User.objects.get(username=email)
            auth_token = Token.objects.get(user=user)
        except ObjectDoesNotExist:
            raise Http404(f'Token not found for this user:{email}')
        response_data = {'token': f'Token {auth_token}'}
        return Response(response_data)


class MasterUserLoans(APIView):
    @staticmethod
    def get_repay_details(master_data):
        amount = master_data['amount']
        term = master_data['term']
        pay = amount / term
        current_date = master_data['date']
        reapay_details = []
        while term > 0:
            reapay_detail = {}
            future_date = current_date + timedelta(days=7)
            repay_loan_date = '%s-%s-%s' % (future_date.year, future_date.month, future_date.day)
            reapay_detail["amount"] = pay
            reapay_detail["status"] = 1
            reapay_detail['date'] = repay_loan_date
            reapay_details.append(reapay_detail)
            current_date = future_date
            term -= 1
        return reapay_details

    def post(self, request, customer_id,  *args, **kwargs):
        user = UserProfile.objects.get(id=customer_id)
        master_data = request.data
        master_data['lastmod'] = datetime.today().date()
        master_data['date'] = master_data.get('loan_date', datetime.today().date())
        master_data['customer'] = customer_id
        master_data['repay_details'] = self.get_repay_details(master_data)
        master_data['status'] = 1
        with transaction.atomic():
            user_loan_serializer = UserLoanSerializer(data=master_data)
            if user_loan_serializer.is_valid(raise_exception=True):
                user = user_loan_serializer.save()
        return Response(user_loan_serializer.data)

    def get(self, request, customer_id, *args, **kwargs):
        loans = Loan.objects.filter(customer__id=customer_id)
        master_loans = UserLoanSerializer(
            loans,
            context={'request': request},
            many=True,
        ).data
        return Response(master_loans)


class MasterUserLoanDetails(APIView):
    def patch(self, request, customer_id, loan_id,  *args, **kwargs):
        try:
            loan = Loan.objects.get(customer_id=customer_id, id=loan_id)
        except ObjectDoesNotExist:
            raise Http404(f'Not found!')
        if loan.status == Loan.STATUS_LOOKUP_BY_VALUE['Pending']:
            raise BadRequest('Waiting for admin approvals.')
        if loan.status == Loan.STATUS_LOOKUP_BY_VALUE['Paid']:
            raise BadRequest('No pending loans available.')
        master_data = request.data
        total_loan_amount = loan.amount
        term = loan.term - 1
        payment_amount = master_data['amount']
        remaining_amount = (total_loan_amount - payment_amount) / term
        requesting_loan_date = datetime.today().date()
        repay_details = loan.repay_details
        for repay_detail in repay_details:
            repay_loan_date = datetime.strptime(repay_detail['date'], "%Y-%m-%d").date()
            if repay_detail['status'] == Loan.STATUS_LOOKUP_BY_VALUE['Pending'] and requesting_loan_date <= repay_loan_date:
                repay_detail['status'] = Loan.STATUS_LOOKUP_BY_VALUE['Paid']
                break

        payment_statuses = []
        for repay_detail in repay_details:
            repay_loan_date = datetime.strptime(repay_detail['date'], "%Y-%m-%d").date()
            if requesting_loan_date > repay_loan_date and repay_detail['status'] == Loan.STATUS_LOOKUP_BY_VALUE['Pending']:
                repay_detail['status'] = Loan.STATUS_LOOKUP_BY_VALUE['Due']

            elif repay_detail['status'] == Loan.STATUS_LOOKUP_BY_VALUE['Paid']:
                pass
            else:
                repay_detail['status'] = Loan.STATUS_LOOKUP_BY_VALUE['Pending']
                repay_detail['amount'] = remaining_amount
            payment_statuses.append(repay_detail['status'])

        is_all_paids = all(payment_status == Loan.STATUS_LOOKUP_BY_VALUE['Paid'] for payment_status in payment_statuses)
        if is_all_paids:
            loan.status = Loan.STATUS_LOOKUP_BY_VALUE['Paid']
        master_loan = UserLoanSerializer(
            loan,
            context={'request': request}
            ).data
        return Response(master_loan)

    def get(self, request, customer_id, loan_id,  *args, **kwargs):
        try:
            loan = Loan.objects.get(customer_id=customer_id, id=loan_id)
        except ObjectDoesNotExist:
            raise Http404('Not found')
        master_loan = UserLoanSerializer(
            loan,
            context={'request': request}
            ).data
        response_data = master_loan
        response_data['status_message'] = Loan.STATUS_LOOKUP[response_data['status']]
        return Response(master_loan)


class MasterAdminLoanApproval(APIView):
    def patch(self, request, customer_id, loan_id, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("You do not have permission to perform this action.")
        status = request.data.get('status')
        if not status or status not in Loan.STATUS_LOOKUP.keys():
            raise BadRequest(f'Invalid status! Valid status are: {list(Loan.STATUS_LOOKUP.keys())}')
        try:
            loan = Loan.objects.get(id=loan_id, customer__id=customer_id)
        except ObjectDoesNotExist:
            raise Http404('Loan details not found.')
        loan.status = Loan.STATUS_LOOKUP_BY_VALUE['Approve']
        with transaction.atomic():
            user_loan_serializer = UserLoanSerializer(
                loan,
                data=request.data,
                partial=True,
            )
            if user_loan_serializer.is_valid(raise_exception=True):
                user = user_loan_serializer.save()
        response_data = user_loan_serializer.data
        response_data['status'] = status
        response_data['status_message'] = Loan.STATUS_LOOKUP[status]
        return Response(response_data)

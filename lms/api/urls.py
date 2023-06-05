from django.urls import path

from api.userprofile.views import (MasterAdminLoanApproval, MasterUserList,
                                   MasterUserLoanDetails, MasterUserLoans,
                                   MasterUserToken)

urlpatterns = [
    path(
        '<str:version>/users/<uuid:customer_id>/loans/<uuid:loan_id>/review',
        MasterAdminLoanApproval.as_view(),
        name='user-loan-review',
    ),
    # Loans
    path(
        '<str:version>/users/<uuid:customer_id>/loans/<uuid:loan_id>',
        MasterUserLoanDetails.as_view(),
        name='user-loan-details',
    ),
    path(
        '<str:version>/users/<uuid:customer_id>/loans',
        MasterUserLoans.as_view(),
        name='user-loans',
    ),
    # Users
    path(
        '<str:version>/users',
        MasterUserList.as_view(),
        name='user-registration',
    ),
    # Tokens
    path(
        '<str:version>/token',
        MasterUserToken.as_view(),
        name='user-token',
    ),
]

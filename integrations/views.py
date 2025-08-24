from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from integrations.permissions import IsExternalSystem
from .serializers import (
    PayrollUploadSerializer,
    PayrollDisbursementSerializer,
    PunchSerializer,
    PunchBulkSerializer,
)

class PayrollUploadJWTView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsExternalSystem]

    @swagger_auto_schema(
        request_body=PayrollUploadSerializer,
        responses={200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                       properties={
                                           "run_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                           "created": openapi.Schema(type=openapi.TYPE_INTEGER),
                                           "updated": openapi.Schema(type=openapi.TYPE_INTEGER),
                                           "errors": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                                       })},
        operation_summary="Upload external payroll (JWT)",
        tags=["Integrations • Payroll"],
    )
    def post(self, request):
        s = PayrollUploadSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = s.save()
        return Response(result, status=status.HTTP_200_OK)

class PayrollDisbursementCallbackJWTView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsExternalSystem]

    @swagger_auto_schema(
        request_body=PayrollDisbursementSerializer,
        responses={200: "OK"},
        operation_summary="Bank disbursement callback (JWT)",
        tags=["Integrations • Payroll"],
    )
    def post(self, request):
        s = PayrollDisbursementSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = s.save()
        return Response(result, status=status.HTTP_200_OK)

class AttendancePunchJWTView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsExternalSystem]

    @swagger_auto_schema(
        request_body=PunchSerializer,
        responses={200: "OK"},
        operation_summary="Single biometric punch (JWT)",
        tags=["Integrations • Attendance"],
    )
    def post(self, request):
        s = PunchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = s.save()
        return Response(result, status=status.HTTP_200_OK)

class AttendanceBulkJWTView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsExternalSystem]

    @swagger_auto_schema(
        request_body=PunchBulkSerializer,
        responses={200: "OK"},
        operation_summary="Bulk biometric punches (JWT)",
        tags=["Integrations • Attendance"],
    )
    def post(self, request):
        s = PunchBulkSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        result = s.save()
        return Response(result, status=status.HTTP_200_OK)

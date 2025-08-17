from datetime import datetime

def get_kst_now():
    """한국 시간(KST) 반환 - 더 이상 사용하지 않음"""
    return datetime.now()  # 시스템 로컬 시간 사용

def get_kst_date_str():
    """한국 시간 기준 날짜 문자열 반환 (YYYY-MM-DD) - 더 이상 사용하지 않음"""
    return datetime.now().strftime("%Y-%m-%d")

def get_kst_datetime_str():
    """한국 시간 기준 날짜시간 문자열 반환 (YYYY-MM-DD HH:MM:SS) - 더 이상 사용하지 않음"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
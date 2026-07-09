# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import false
from typing import Optional, List
from pydantic import BaseModel, Field
from database import get_db, SessionLocal
from models import User, Course, Teacher, Student, Room, Settings, PasswordResetRequest, RegistrationToken
from schemas import UserCreate, UserLogin, Token, User as UserSchema, UserManagementCreate, UserManagementUpdate, PasswordChange, PasswordVerify, PasswordResetRequest as PasswordResetRequestSchema, PasswordResetRequestCreate, PasswordResetRequestUpdate, PasswordReset
from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from utils.logger import log_operation
import os
import json
import uuid

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def check_teacher_visibility(db: Session, current_user: User) -> bool:
    """检查导师可见性限制是否开启"""
    settings = db.query(Settings).first()
    
    if not settings or not settings.teacher_visibility_restricted:
        return False
    if current_user.role not in ['teacher', 'course_admin']:
        return False
    return True

def is_subject_teacher(db: Session, current_user: User) -> bool:
    """检查当前用户是否为超级导师"""
    import json
    settings = db.query(Settings).first()
    if not settings or not settings.subject_teachers:
        return False
    
    try:
        # 确保将 JSON 字符串解析为整数列表
        raw_data = json.loads(settings.subject_teachers)
        if isinstance(raw_data, list):
            super_teacher_ids = [int(x) for x in raw_data]
        else:
            super_teacher_ids = []
    except (json.JSONDecodeError, TypeError, ValueError):
        super_teacher_ids = []
    
    if not super_teacher_ids:
        return False
    
    if not current_user.teacher_id:
        return False
    
    return current_user.teacher_id in super_teacher_ids

def can_edit_completed_schedule(db: Session, current_user: User, schedule_execution_status: str) -> bool:
    """检查用户是否可以编辑已完成/延期/取消的课程安排"""
    if schedule_execution_status not in ['completed', 'postponed', 'cancelled']:
        return True
    
    if current_user.role == 'super_admin':
        return True
    
    if not is_subject_teacher(db, current_user):
        return False
    
    settings = db.query(Settings).first()
    if not settings:
        return False
    
    if settings.schedule_edit_restricted:
        return False
    
    return True

def can_delete_completed_schedule(db: Session, current_user: User, schedule_execution_status: str) -> bool:
    """检查用户是否可以删除已完成/延期/取消的课程安排"""
    if schedule_execution_status not in ['completed', 'postponed', 'cancelled']:
        return True
    
    if current_user.role == 'super_admin':
        return True
    
    if not is_subject_teacher(db, current_user):
        return False
    
    settings = db.query(Settings).first()
    if not settings:
        return False
    
    if settings.schedule_delete_restricted:
        return False
    
    return True

def get_teacher_visibility_filter(db: Session, current_user: User):
    """获取导师可见性过滤条件"""
    if not check_teacher_visibility(db, current_user):
        return None 
    
    if is_subject_teacher(db, current_user):
        return None 
    
    if not current_user.teacher_id:
        log_operation(db, "用户认证", "获取导师可见性过滤条件", f"警告：开启了限制但用户未绑定导师，将隐藏所有数据", current_user.username, "WARNING")
        return false() 
    
    return current_user.teacher_id

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def _ldap_determine_role(user_entry, ldap_config: dict) -> str:
    """根据LDAP用户条目和配置确定系统角色"""
    role = ldap_config.get('default_role', 'course_admin')
    role_mapping_type = ldap_config.get('role_mapping_type', 'default')
    
    if role_mapping_type != 'attribute':
        return role
    
    role_mappings = ldap_config.get('role_mappings', {})
    role_mapping_attribute = ldap_config.get('role_mapping_attribute', 'ou')
    
    if role_mapping_attribute == 'ou':
        user_ou = str(user_entry.ou) if hasattr(user_entry, 'ou') else ''
        if user_ou:
            for sys_role, ldap_value in role_mappings.items():
                if ldap_value and ldap_value in user_ou:
                    role = sys_role
                    break
    elif role_mapping_attribute == 'memberOf':
        user_groups = []
        if hasattr(user_entry, 'memberOf'):
            user_groups = [str(group) for group in user_entry.memberOf]
        for sys_role, ldap_value in role_mappings.items():
            if ldap_value and any(ldap_value in group for group in user_groups):
                role = sys_role
                break
    elif role_mapping_attribute == 'custom':
        custom_attr = ldap_config.get('custom_attribute_name', '')
        if custom_attr and hasattr(user_entry, custom_attr):
            attr_value = str(getattr(user_entry, custom_attr))
            for sys_role, ldap_value in role_mappings.items():
                if ldap_value and ldap_value in attr_value:
                    role = sys_role
                    break
    
    return role


def _ldap_get_search_attributes(ldap_config: dict) -> list:
    """根据角色映射类型决定需要获取的LDAP属性"""
    role_mapping_type = ldap_config.get('role_mapping_type', 'default')
    search_attributes = ['cn', 'mail', 'displayName']
    
    if role_mapping_type == 'attribute':
        role_mapping_attribute = ldap_config.get('role_mapping_attribute', 'ou')
        search_attributes.extend(['memberOf', 'ou'])
        if role_mapping_attribute == 'custom':
            custom_attr = ldap_config.get('custom_attribute_name', '')
            if custom_attr:
                search_attributes.append(custom_attr)
    
    return list(set(search_attributes))


def _ldap_extract_user_info(user_entry, username: str, role: str) -> dict:
    """从LDAP用户条目中提取用户信息"""
    display_name = username
    if hasattr(user_entry, 'displayName'):
        val = str(user_entry.displayName)
        if val and val != '[]':
            display_name = val
    
    email = ''
    if hasattr(user_entry, 'mail'):
        val = str(user_entry.mail)
        if val and val != '[]':
            email = val
    
    return {
        'username': username,
        'display_name': display_name,
        'email': email,
        'role': role
    }


def authenticate_ldap(username: str, password: str, db: Session) -> tuple[bool, Optional[dict]]:
    """LDAP认证函数
    返回: (认证成功, 用户信息字典)
    """
    try:
        settings = db.query(Settings).first()
        if not settings or not settings.ldap_enabled:
            return False, None
        
        ldap_config = json.loads(settings.ldap_config) if settings.ldap_config else {}
        
        if not ldap_config.get('enabled', False):
            return False, None
        
        import ldap3
        
        server = ldap_config.get('server', '')
        port = ldap_config.get('port', 389)
        use_ssl = ldap_config.get('use_ssl', False)
        bind_dn = ldap_config.get('bind_dn', '')
        bind_password = ldap_config.get('bind_password', '')
        user_search_base = ldap_config.get('user_search_base', '')
        user_search_filter = ldap_config.get('user_search_filter', '(uid={username})')
        user_dn_template = ldap_config.get('user_dn_template', '')
        
        if not server:
            log_operation(db, "用户认证", "LDAP认证失败", "LDAP服务器地址未配置", username, "WARNING")
            return False, None
        
        server_uri = f"{'ldaps' if use_ssl else 'ldap'}://{server}:{port}"
        server_obj = ldap3.Server(server_uri, get_info=ldap3.DSA)
        
        conn = None
        try:
            if bind_dn and bind_password:
                try:
                    conn = ldap3.Connection(server_obj, user=bind_dn, password=bind_password, auto_bind=True)
                except ldap3.core.exceptions.LDAPBindError as e:
                    log_operation(db, "用户认证", "LDAP认证失败", f"LDAP管理员绑定失败: {str(e)}", username, "WARNING")
                    return False, None
                except Exception as e:
                    log_operation(db, "用户认证", "LDAP认证失败", f"LDAP管理员绑定失败: {str(e)}", username, "WARNING")
                    return False, None
            else:
                conn = ldap3.Connection(server_obj)
                if not conn.bind():
                    log_operation(db, "用户认证", "LDAP认证失败", f"LDAP匿名绑定失败: {conn.result['description']}", username, "WARNING")
                    conn.unbind()
                    return False, None
            
            if user_dn_template:
                user_dn = user_dn_template.format(username=username)
                
                if user_search_base:
                    search_filter = user_search_filter.format(username=username)
                    search_attributes = _ldap_get_search_attributes(ldap_config)
                    
                    try:
                        conn.search(search_base=user_search_base, search_filter=search_filter, attributes=search_attributes)
                    except Exception as e:
                        log_operation(db, "用户认证", "LDAP认证", f"DN模板模式下搜索用户信息失败: {str(e)}，将使用默认信息", username, "WARNING")
                    
                    if conn.entries:
                        user_entry = conn.entries[0]
                        role = _ldap_determine_role(user_entry, ldap_config)
                        user_info = _ldap_extract_user_info(user_entry, username, role)
                    else:
                        role = ldap_config.get('default_role', 'course_admin')
                        user_info = {'username': username, 'display_name': username, 'email': '', 'role': role}
                else:
                    role = ldap_config.get('default_role', 'course_admin')
                    user_info = {'username': username, 'display_name': username, 'email': '', 'role': role}
                
                conn.unbind()
                conn = None
                
                try:
                    user_conn = ldap3.Connection(server_obj, user=user_dn, password=password, auto_bind=True)
                    user_conn.unbind()
                    log_operation(db, "用户认证", "LDAP认证成功", f"用户 {username} LDAP认证成功，角色: {role}", username, "INFO")
                    return True, user_info
                except ldap3.core.exceptions.LDAPBindError as e:
                    log_operation(db, "用户认证", "LDAP认证失败", f"用户 {username} LDAP认证失败(密码错误): {str(e)}", username, "WARNING")
                    return False, None
                except Exception as e:
                    log_operation(db, "用户认证", "LDAP认证失败", f"用户 {username} LDAP认证失败: {str(e)}", username, "WARNING")
                    return False, None
            else:
                if not user_search_base:
                    log_operation(db, "用户认证", "LDAP认证失败", "未配置用户搜索基础DN(user_search_base)且未配置用户DN模板(user_dn_template)", username, "WARNING")
                    if conn:
                        conn.unbind()
                    return False, None
                
                search_filter = user_search_filter.format(username=username)
                search_attributes = _ldap_get_search_attributes(ldap_config)
                
                conn.search(search_base=user_search_base, search_filter=search_filter, attributes=search_attributes)
                
                if not conn.entries:
                    log_operation(db, "用户认证", "LDAP认证失败", f"用户 {username} 在LDAP中不存在(搜索基础: {user_search_base}, 过滤器: {search_filter})", username, "WARNING")
                    conn.unbind()
                    return False, None
                
                user_dn = conn.entries[0].entry_dn
                user_entry = conn.entries[0]
                role = _ldap_determine_role(user_entry, ldap_config)
                user_info = _ldap_extract_user_info(user_entry, username, role)
                conn.unbind()
                conn = None
                
                try:
                    user_conn = ldap3.Connection(server_obj, user=user_dn, password=password, auto_bind=True)
                    user_conn.unbind()
                    log_operation(db, "用户认证", "LDAP认证成功", f"用户 {username} LDAP认证成功，角色: {role}", username, "INFO")
                    return True, user_info
                except ldap3.core.exceptions.LDAPBindError as e:
                    log_operation(db, "用户认证", "LDAP认证失败", f"用户 {username} LDAP认证失败(密码错误): {str(e)}", username, "WARNING")
                    return False, None
                except Exception as e:
                    log_operation(db, "用户认证", "LDAP认证失败", f"用户 {username} LDAP认证失败: {str(e)}", username, "WARNING")
                    return False, None
        finally:
            if conn is not None:
                try:
                    conn.unbind()
                except Exception:
                    pass
                
    except ImportError:
        log_operation(db, "用户认证", "LDAP认证失败", "ldap3库未安装，请运行: pip install ldap3", username, "ERROR")
        return False, None
    except Exception as e:
        log_operation(db, "用户认证", "LDAP认证失败", f"LDAP认证异常: {str(e)}", username, "ERROR")
        return False, None

def get_password_hash(password):
    return pwd_context.hash(password)

def _get_session_timeout_minutes(db: Session = None) -> int:
    """从系统设置中读取登录超时时间（分钟）"""
    default = 1440
    if db is None:
        return default
    try:
        settings = db.query(Settings).first()
        if settings and settings.session_timeout_minutes:
            return max(5, min(settings.session_timeout_minutes, 43200))
    except Exception:
        pass
    return default

def create_access_token(data: dict, expires_delta: timedelta = None, db: Session = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        timeout_minutes = _get_session_timeout_minutes(db)
        expire = datetime.now() + timedelta(minutes=timeout_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            log_operation(db, "用户认证", "验证凭据", "无法验证凭据", username, "ERROR")
            raise credentials_exception
    except ExpiredSignatureError:
        username = "unknown"
        try:
            unverified_payload = jwt.get_unverified_claims(token)
            username = unverified_payload.get("sub", "unknown")
        except Exception:
            pass
        log_operation(db, "用户认证", "验证凭据", f"Token已过期，用户: {username}", username, "WARNING")
        raise credentials_exception
    except JWTError:
        log_operation(db, "用户认证", "验证凭据", "JWT解码失败，Token无效或被篡改", "unknown", "ERROR")
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        log_operation(db, "用户认证", "验证凭据", f"用户 {username} 不存在，无法验证凭据", username, "ERROR")
        raise credentials_exception
    return user

def get_current_superadmin_user(current_user: User = Depends(get_current_user)):
    """超级管理员权限检查"""
    if current_user.role != 'super_admin':
        log_operation(None, "用户认证", "检查超级管理员权限", f"权限不足，当前角色: {current_user.role}", current_user.username, "WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

def get_current_system_admin_user(current_user: User = Depends(get_current_user)):
    """系统管理员权限检查"""
    if current_user.role not in ['super_admin', 'system_admin']:
        log_operation(None, "用户认证", "检查系统管理员权限", f"权限不足，当前角色: {current_user.role}", current_user.username, "WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

def get_current_course_admin_user(current_user: User = Depends(get_current_user)):
    """课程管理员权限检查"""
    if current_user.role not in ['super_admin', 'course_admin']:
        log_operation(None, "用户认证", "检查课程管理员权限", f"权限不足，当前角色: {current_user.role}", current_user.username, "WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user
    
def get_current_system_audit_user(current_user: User = Depends(get_current_user)):
    """系统审计员权限检查"""
    if current_user.role not in ['super_admin', 'system_audit']:
        log_operation(None, "用户认证", "检查系统审计员权限", f"权限不足，当前角色: {current_user.role}", current_user.username, "WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

@router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_system_admin_user)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        log_operation(db, "用户认证", "注册失败", f"用户名已存在: {user.username}", user.username, "WARNING")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        role='course_admin'
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log_operation(db, "用户", "注册", f"用户注册成功: {user.username}", current_user.username)
    return db_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 先尝试LDAP认证
    ldap_success, ldap_user_info = authenticate_ldap(form_data.username, form_data.password, db)
    
    if ldap_success:
        # LDAP认证成功
        if not user:
            # 如果用户不存在，创建新用户
            ldap_role = ldap_user_info.get('role', 'course_admin')
            
            user = User(
                username=form_data.username,
                password_hash=get_password_hash(form_data.password),  # 保存密码以备后用
                role=ldap_role
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log_operation(db, "用户", "LDAP登录创建", f"LDAP认证成功，自动创建用户: {form_data.username}, 角色: {ldap_role}", form_data.username)
        else:
            # 更新用户密码（保持同步）
            user.password_hash = get_password_hash(form_data.password)
            # 更新用户角色（如果LDAP返回了角色信息）
            ldap_role = ldap_user_info.get('role')
            if ldap_role and ldap_role != user.role:
                old_role = user.role
                user.role = ldap_role
                log_operation(db, "用户", "LDAP登录", f"LDAP认证成功，更新用户角色: {form_data.username}, {old_role} -> {ldap_role}", form_data.username)
            else:
                log_operation(db, "用户", "LDAP登录", f"LDAP认证成功: {form_data.username}", form_data.username)
            db.commit()
    elif user and verify_password(form_data.password, user.password_hash):
        # 本地密码验证成功
        log_operation(db, "用户", "登录", f"本地认证成功: {form_data.username}", form_data.username)
    else:
        # 认证失败
        log_operation(db, "用户认证", "登录失败", f"用户名或密码错误: {form_data.username}", form_data.username, "WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username}, db=db
    )
    
    # 检查是否为超级导师
    is_subject_teacher_flag = is_subject_teacher(db, user)
    
    log_operation(db, "用户", "登录", f"用户登录成功: {user.username}, 超级导师: {is_subject_teacher_flag}", user.username)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user,
        "is_admin": user.role in ['super_admin', 'system_admin'],
        "is_subject_teacher": is_subject_teacher_flag,
        "must_change_password": getattr(user, 'must_change_password', False)
    }

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh")
def refresh_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """续期Token：当前Token有效时，签发新Token延长过期时间"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

# 修改后
@router.get("", response_model=List[UserSchema])
def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)  # ✅ super_admin和system_admin都可以访问
):
    query = db.query(User)
    if search:
        query = query.filter(User.username.contains(search))
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/password-reset-requests", response_model=List[PasswordResetRequestSchema])
def get_password_reset_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """管理员获取所有密码重置请求"""
    requests = db.query(PasswordResetRequest).order_by(PasswordResetRequest.created_at.desc()).all()
    return requests

@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        log_operation(db, "用户认证", "获取用户详情失败", f"用户ID {user_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

@router.post("", response_model=UserSchema)
def create_user(
    user_data: UserManagementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin_user)
):
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        log_operation(db, "用户认证", "创建用户失败", f"用户名已存在: {user_data.username}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        teacher_id=user_data.teacher_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log_operation(db, "用户", "新增", f"成功创建用户: {user_data.username}", current_user.username)
    return db_user

@router.put("/password-reset-requests/{request_id}")
def update_password_reset_request(
    request_id: int,
    request_update: PasswordResetRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    """管理员更新密码重置请求状态"""
    reset_request = db.query(PasswordResetRequest).filter(PasswordResetRequest.id == request_id).first()
    if not reset_request:
        log_operation(db, "用户认证", "更新密码重置请求失败", f"重置请求ID {request_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="重置请求不存在")
    
    reset_request.status = request_update.status
    db.commit()
    db.refresh(reset_request)
    log_operation(db, "用户", "密码", f"成功更新密码重置请求: {reset_request.username} - {request_update.status}", current_user.username)
    return reset_request

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_data: UserManagementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_system_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        log_operation(db, "用户认证", "更新用户失败", f"用户ID {user_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)
    if user_data.role is not None:
        user.role = user_data.role
    if hasattr(user_data, 'teacher_id'):
        if user_data.role != 'course_admin':
            user.teacher_id = None
        else:
            user.teacher_id = user_data.teacher_id
    
    db.commit()
    db.refresh(user)
    log_operation(db, "用户", "更新", f"成功更新用户: {user.username}", current_user.username)
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin_user)
):
    if user_id == current_user.id:
        log_operation(db, "用户认证", "删除用户失败", f"尝试删除当前登录用户: {current_user.username}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        log_operation(db, "用户认证", "删除用户失败", f"用户ID {user_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    db.delete(user)
    db.commit()
    log_operation(db, "用户", "删除", f"删除用户: {user.username}", current_user.username, "WARNING")
    return {"message": "删除成功"}

@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        log_operation(db, "用户认证", "修改密码失败", f"旧密码错误，用户: {current_user.username}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    # 验证两次新密码是否一致
    if password_data.new_password != password_data.confirm_password:
        log_operation(db, "用户认证", "修改密码失败", f"两次输入的新密码不一致，用户: {current_user.username}", current_user.username, "WARNING")
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    if hasattr(current_user, 'must_change_password'):
        current_user.must_change_password = False
    db.commit()
    log_operation(db, "用户", "更新", f"成功修改密码: {current_user.username}", current_user.username)
    return {"message": "密码修改成功"}

@router.post("/verify-password")
def verify_current_password(
    password_data: PasswordVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证当前用户密码"""
    is_valid = verify_password(password_data.password, current_user.password_hash)
    log_operation(db, "用户认证", "密码验证", f"用户: {current_user.username}, 验证结果: {is_valid}", current_user.username, "DEBUG")
    return {"valid": is_valid}

@router.post("/forgot-password")
def forgot_password(
    request: PasswordResetRequestCreate,
    db: Session = Depends(get_db)
):
    """用户忘记密码，发送重置请求给管理员"""
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        log_operation(db, "用户认证", "发送密码重置请求失败", f"用户名 {request.username} 不存在", request.username, "WARNING")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已有待处理的请求
    existing_request = db.query(PasswordResetRequest).filter(
        PasswordResetRequest.username == request.username,
        PasswordResetRequest.status == 'pending'
    ).first()
    
    if existing_request:
        log_operation(db, "用户认证", "发送密码重置请求失败", f"用户 {request.username} 已有待处理的密码重置请求", request.username, "WARNING")
        raise HTTPException(status_code=400, detail="您已有待处理的密码重置请求，请等待管理员处理")
    
    reset_request = PasswordResetRequest(
        user_id=user.id,
        username=request.username,
        status='pending'
    )
    db.add(reset_request)
    db.commit()
    db.refresh(reset_request)
    log_operation(db, "用户", "密码", f"用户已发送密码重置申请: {request.username}", request.username)
    return {"message": "密码重置请求已发送给管理员，请等待处理"}

@router.post("/reset-password/{user_id}")
def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superadmin_user)
):
    """管理员重置用户密码"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        log_operation(db, "用户认证", "重置用户密码失败", f"用户ID {user_id} 不存在", current_user.username, "WARNING")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    log_operation(db, "用户", "密码", f"管理员重置用户密码: {user.username}", current_user.username, "WARNING")
    return {"message": "密码重置成功"}


class OpenRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")

class ConfirmRegistrationRequest(BaseModel):
    token: str = Field(..., description="确认令牌")


def _check_open_registration(db: Session) -> Settings:
    settings = db.query(Settings).first()
    if not settings or not settings.open_registration_enabled:
        raise HTTPException(status_code=403, detail="开放注册未启用")
    if settings.open_registration_expiry and datetime.now() > settings.open_registration_expiry:
        settings.open_registration_enabled = False
        db.commit()
        raise HTTPException(status_code=403, detail="开放注册已过期")
    return settings


@router.post("/open-register")
def open_register(
    request: OpenRegistrationRequest,
    db: Session = Depends(get_db)
):
    settings = _check_open_registration(db)

    if not request.email or '@' not in request.email:
        raise HTTPException(status_code=400, detail="请输入有效的邮箱地址")

    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    existing_email = db.query(RegistrationToken).filter(
        RegistrationToken.email == request.email,
        RegistrationToken.is_used == False
    ).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="该邮箱已提交注册申请，请查收确认邮件")

    existing_user_by_email = db.query(User).filter(User.username == request.email).first()
    if existing_user_by_email:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    token = str(uuid.uuid4())
    password_hash = get_password_hash(request.password)
    expires_at = datetime.now() + timedelta(hours=24)

    reg_token = RegistrationToken(
        email=request.email,
        username=request.username,
        password_hash=password_hash,
        token=token,
        is_used=False,
        expires_at=expires_at
    )
    db.add(reg_token)
    db.commit()

    try:
        email_config = json.loads(settings.email_config or '{}')
        if not email_config.get('smtp_host'):
            db.delete(reg_token)
            db.commit()
            raise HTTPException(status_code=500, detail="系统邮件服务未配置，无法发送确认邮件，请联系管理员")

        site_url = settings.site_url or ''
        confirm_url = f"{site_url}/api/auth/confirm-registration?token={token}"

        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.utils import formataddr

        msg = MIMEMultipart()
        msg['From'] = formataddr((email_config.get('smtp_from_name', settings.site_name), email_config.get('smtp_user', '')))
        msg['To'] = request.email
        msg['Subject'] = f"【{settings.site_name}】注册确认邮件"

        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .btn {{ display: inline-block; padding: 12px 30px; background: #409eff; color: white; text-decoration: none; border-radius: 5px; margin: 15px 0; }}
                .footer {{ margin-top: 20px; text-align: center; color: #909399; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>注册确认</h2>
                </div>
                <div class="content">
                    <p>您好，<strong>{request.username}</strong>：</p>
                    <p>您正在注册 <strong>{settings.site_name}</strong> 课程管理系统账户。</p>
                    <p>请点击下方按钮确认您的注册：</p>
                    <div style="text-align: center;">
                        <a href="{confirm_url}" class="btn">确认注册</a>
                    </div>
                    <p style="color: #909399; font-size: 13px;">如果按钮无法点击，请复制以下链接到浏览器打开：</p>
                    <p style="word-break: break-all; font-size: 13px; color: #409eff;">{confirm_url}</p>
                    <p style="color: #E6A23C; font-size: 13px;">⚠ 此链接24小时内有效，过期需重新注册。</p>
                    <p style="color: #909399; font-size: 13px;">如果您没有进行此操作，请忽略此邮件。</p>
                </div>
                <div class="footer">
                    <p>{settings.site_name} · 课程安排系统</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html', 'utf-8'))

        if email_config.get('smtp_ssl', True):
            smtp = smtplib.SMTP_SSL(email_config.get('smtp_host', ''), email_config.get('smtp_port', 465))
        else:
            smtp = smtplib.SMTP(email_config.get('smtp_host', ''), email_config.get('smtp_port', 465))
        smtp.login(email_config.get('smtp_user', ''), email_config.get('smtp_password', ''))
        smtp.send_message(msg)
        smtp.quit()

        log_operation(db, "用户认证", "开放注册", f"用户 {request.username} 提交注册申请，确认邮件已发送至 {request.email}", request.username, "INFO")
    except HTTPException:
        raise
    except Exception as e:
        db.delete(reg_token)
        db.commit()
        log_operation(db, "用户认证", "开放注册失败", f"发送确认邮件失败: {str(e)}", request.username, "ERROR")
        raise HTTPException(status_code=500, detail=f"发送确认邮件失败: {str(e)}，请联系管理员")

    return {"message": "注册申请已提交，请查收邮箱确认邮件完成注册"}


@router.get("/confirm-registration")
def confirm_registration(
    token: str,
    db: Session = Depends(get_db)
):
    settings = _check_open_registration(db)

    reg_token = db.query(RegistrationToken).filter(
        RegistrationToken.token == token,
        RegistrationToken.is_used == False
    ).first()

    if not reg_token:
        html_content = """
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><style>
        body{font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f7fa;}
        .card{background:white;padding:40px;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center;max-width:400px;}
        .icon{font-size:48px;color:#F56C6C;}
        h2{color:#303133;margin:15px 0 10px;}
        p{color:#909399;line-height:1.6;}
        </style></head><body>
        <div class="card"><div class="icon">✗</div><h2>注册确认失败</h2><p>确认链接无效或已使用，请重新注册。</p></div>
        </body></html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    if datetime.now() > reg_token.expires_at:
        db.delete(reg_token)
        db.commit()
        html_content = """
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><style>
        body{font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f7fa;}
        .card{background:white;padding:40px;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center;max-width:400px;}
        .icon{font-size:48px;color:#E6A23C;}
        h2{color:#303133;margin:15px 0 10px;}
        p{color:#909399;line-height:1.6;}
        </style></head><body>
        <div class="card"><div class="icon">⏰</div><h2>确认链接已过期</h2><p>确认链接已过期，请重新注册。</p></div>
        </body></html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    existing_user = db.query(User).filter(User.username == reg_token.username).first()
    if existing_user:
        reg_token.is_used = True
        db.commit()
        html_content = """
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8"><style>
        body{font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f7fa;}
        .card{background:white;padding:40px;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center;max-width:400px;}
        .icon{font-size:48px;color:#E6A23C;}
        h2{color:#303133;margin:15px 0 10px;}
        p{color:#909399;line-height:1.6;}
        </style></head><body>
        <div class="card"><div class="icon">⚠</div><h2>用户名已存在</h2><p>该用户名已被注册，请使用其他用户名重新注册。</p></div>
        </body></html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    new_user = User(
        username=reg_token.username,
        password_hash=reg_token.password_hash,
        role='course_admin',
        is_admin=False,
        must_change_password=False
    )
    db.add(new_user)
    reg_token.is_used = True
    db.commit()

    log_operation(db, "用户认证", "开放注册确认", f"用户 {reg_token.username} 通过开放注册成功创建账户", reg_token.username, "INFO")

    site_url = settings.site_url or ''
    login_url = f"{site_url}/admin/login" if site_url else '/admin/login'

    html_content = f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><style>
    body{{font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f5f7fa;}}
    .card{{background:white;padding:40px;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center;max-width:400px;}}
    .icon{{font-size:48px;color:#67C23A;}}
    h2{{color:#303133;margin:15px 0 10px;}}
    p{{color:#909399;line-height:1.6;}}
    .btn{{display:inline-block;padding:12px 30px;background:#409eff;color:white;text-decoration:none;border-radius:5px;margin-top:15px;}}
    </style></head><body>
    <div class="card"><div class="icon">✓</div><h2>注册成功！</h2><p>您的账户已创建成功，角色为<strong>课程管理员</strong>。</p><p>请使用用户名 <strong>{reg_token.username}</strong> 登录系统。</p><a href="{login_url}" class="btn">前往登录</a></div>
    </body></html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)


@router.get("/open-registration-status")
def get_open_registration_status(db: Session = Depends(get_db)):
    import logging as _logging
    _logger = _logging.getLogger("open_registration")
    try:
        settings = db.query(Settings).first()
        if not settings:
            _logger.warning("[开放注册] 未找到系统设置记录")
            return {"enabled": False}
        
        enabled = getattr(settings, 'open_registration_enabled', False)
        expiry = getattr(settings, 'open_registration_expiry', None)
        
        _logger.info(f"[开放注册] enabled={enabled}, expiry={expiry}, now={datetime.now()}")
        
        if not enabled:
            _logger.info("[开放注册] 开放注册未启用，返回enabled=False")
            return {"enabled": False}

        if expiry and datetime.now() > expiry:
            settings.open_registration_enabled = False
            db.commit()
            _logger.warning(f"[开放注册] 开放注册已过期，已自动关闭。expiry={expiry}")
            return {"enabled": False}

        remaining = None
        if expiry:
            remaining = int((expiry - datetime.now()).total_seconds())

        _logger.info(f"[开放注册] 开放注册已启用，返回enabled=True, remaining={remaining}")
        return {
            "enabled": True,
            "expiry": expiry.isoformat() if expiry else None,
            "remaining_seconds": remaining
        }
    except Exception as e:
        _logger.error(f"[开放注册] 检查开放注册状态失败: {e}", exc_info=True)
        return {"enabled": False}
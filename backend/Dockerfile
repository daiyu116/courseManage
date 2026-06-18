# ============================================================
# 阶段1：构建 — Cython 编译关键模块
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir -i https://pypi.org/simple/ -r requirements.txt
RUN pip install --no-cache-dir cython || \
    pip install --no-cache-dir -i https://pypi.org/simple/ cython

COPY . .

RUN python setup_cython.py build_ext --inplace

RUN CRITICAL_MODULES="utils/license.py routers/license.py optimizer.py utils/smart_command.py utils/wechat_notifier.py utils/remainder.py" && \
    for f in $CRITICAL_MODULES; do \
        rm -f "$f" && rm -f "${f%.py}.c"; \
    done

RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
RUN find . -type f -name "*.pyc" -delete 2>/dev/null || true
RUN rm -rf build/ setup_cython.py

# ============================================================
# 阶段2：运行 — 仅复制编译产物，不含源码和编译工具链
# ============================================================
FROM python:3.11-slim

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir -i https://pypi.org/simple/ -r requirements.txt

COPY --from=builder /app/ .

RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
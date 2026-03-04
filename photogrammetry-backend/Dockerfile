# ============================================================
# Stage 1: Build OpenSfM from source
# ============================================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libceres-dev \
    libeigen3-dev \
    libopencv-dev \
    libgflags-dev \
    libgoogle-glog-dev \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

# Pin to a known-good commit for reproducibility
RUN git clone --recurse-submodules https://github.com/mapillary/OpenSfM.git /opt/OpenSfM \
    && cd /opt/OpenSfM \
    && git checkout 732ee4ea

WORKDIR /opt/OpenSfM

# Install Python deps first
RUN pip3 install --no-cache-dir scikit-build-core pybind11 numpy

# Build with make (not ninja) and single job to avoid OOM
RUN pip3 install --no-cache-dir \
    --config-settings=cmake.define.CMAKE_BUILD_TYPE=Release \
    --config-settings=cmake.args=-DCMAKE_JOB_POOLS:STRING="compile=1;link=1" \
    --config-settings=build-dir=/tmp/osfm-build \
    -v .

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM ubuntu:22.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    libceres2 \
    libgoogle-glog0v5 \
    libgflags2.2 \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed OpenSfM package and its dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /opt/OpenSfM/bin /opt/OpenSfM/bin

# Add OpenSfM to PATH
ENV PATH="/opt/OpenSfM/bin:${PATH}"

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]

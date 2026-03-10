# ============================================================
# Stage 1: Build COLMAP + OpenMVS from source (CPU-only)
# ============================================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Common build dependencies (shared by COLMAP and OpenMVS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    ca-certificates \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libboost-iostreams-dev \
    libboost-serialization-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libsqlite3-dev \
    libceres-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libopencv-dev \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Build COLMAP ──
RUN git clone --branch 3.9.1 --depth 1 https://github.com/colmap/colmap.git /opt/colmap

WORKDIR /opt/colmap/build

RUN cmake .. -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DCUDA_ENABLED=OFF \
    -DGUI_ENABLED=OFF \
    -DCGAL_ENABLED=ON \
    && ninja -j2 \
    && ninja install

# ── Build VCGLib (header-only, required by OpenMVS) ──
RUN git clone --depth 1 https://github.com/cnr-isti-vclab/vcglib.git /opt/vcglib

# ── Build OpenMVS ──
RUN git clone --branch v2.3.0 --depth 1 https://github.com/cdcseacave/openMVS.git /opt/openMVS

WORKDIR /opt/openMVS/build

RUN cmake .. -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DVCG_ROOT=/opt/vcglib \
    -DOpenMVS_USE_CUDA=OFF \
    -DOpenMVS_USE_OPENGL=OFF \
    && ninja -j2 \
    && ninja install

# ============================================================
# Stage 2: Runtime
# ============================================================
FROM ubuntu:22.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libboost-iostreams-dev \
    libboost-serialization-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libsqlite3-dev \
    libceres-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy COLMAP binary and libraries from builder
COPY --from=builder /usr/local/bin/colmap /usr/local/bin/colmap

# Copy OpenMVS binaries
COPY --from=builder /usr/local/bin/OpenMVS /usr/local/bin/OpenMVS

# Copy all shared libraries
COPY --from=builder /usr/local/lib/ /usr/local/lib/
RUN ldconfig

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "2"]

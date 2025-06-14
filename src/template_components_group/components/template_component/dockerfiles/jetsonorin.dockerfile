FROM public.ecr.aws/d9f6h1v9/raya.core.base_images.ubuntu.20.04_l4t.35.3.1_ros.humble:jetsonorin.4.37

ENV SHELL=/bin/bash
SHELL ["/bin/bash", "-c"]

ENV LOAD_SHARED_PACKAGES=true

RUN sed -i 's/PRELOAD_SHARED_LIBRARIES_DELAY=30/PRELOAD_SHARED_LIBRARIES_DELAY=1/' /setup_env.bash

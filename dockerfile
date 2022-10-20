FROM python:3.8

RUN mkdir /app
COPY protobufs /app/protobufs
COPY generic-python3-comp/editables /app/generic-python3-comp/editables
COPY generic-python3-comp/component.py /app/generic-python3-comp/
COPY generic-python3-comp/component_api.py /app/generic-python3-comp/
COPY generic-python3-comp/requirements.txt /app/generic-python3-comp/
COPY generic-python3-comp/README.md /app/generic-python3-comp/
COPY generic-python3-comp/VERSION /app/generic-python3-comp/
COPY generic-python3-comp/LICENSE /app/generic-python3-comp/
WORKDIR /app/generic-python3-comp

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I ../protobufs --python_out=. --grpc_python_out=. ../protobufs/component.proto

EXPOSE 50060
ENTRYPOINT [ "python", "component_api.py" ]
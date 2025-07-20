FROM langchain/langgraph-api:3.12



# -- Adding local package . --
ADD . /deps/application
# -- End of local package . --

# -- Installing all local dependencies --
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r /deps/application/requirements.txt
# -- End of local dependencies install --
ENV LANGSERVE_GRAPHS='{"agent": "/deps/application/src/agent/graph.py:graph"}'



# -- Ensure user deps didn't inadvertently overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license &&     touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --
# -- Removing pip from the final image ~<:===~~~ --
RUN pip uninstall -y pip setuptools wheel &&     rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* &&     find /usr/local/bin -name "pip*" -delete
# -- End of pip removal --

WORKDIR /deps/application/src
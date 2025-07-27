from pathlib import Path

import requests
import streamlit as st
import yaml

# 页面标题和说明
st.title("OpenAPI Schema 生成工具")
st.markdown("""
从 API 端点获取 OpenAPI schema，选择需要的路径和方法，生成新的 API schema 文件。
""")


# 获取原始 schema 的函数
def fetch_openapi_schema(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        # 直接解析YAML内容
        return yaml.safe_load(response.text)
    except Exception as e:
        st.error(f"获取 schema 失败: {str(e)}")
        return None


# 递归查找所有引用的 schemas
def find_referenced_schemas(obj, found_schemas=None):
    if found_schemas is None:
        found_schemas = set()

    if isinstance(obj, dict):
        if "$ref" in obj:
            ref_path = obj["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                if schema_name not in found_schemas:
                    found_schemas.add(schema_name)
        else:
            for value in obj.values():
                found_schemas = find_referenced_schemas(value, found_schemas)
    elif isinstance(obj, list):
        for item in obj:
            found_schemas = find_referenced_schemas(item, found_schemas)

    return found_schemas


# 从本地获取 schema
schema_url = "http://127.0.0.1:8000/schema"
schema_data = fetch_openapi_schema(schema_url)

if schema_data:
    # 提取所有路径和方法
    paths = schema_data.get("paths", {})

    if not paths:
        st.warning("Schema中没有找到任何路径(paths)")
    else:
        # 显示路径选择器
        st.subheader("选择 API 路径")
        selected_paths = st.multiselect(
            "选择需要包含的路径:",
            options=list(paths.keys()),
            default=list(paths.keys())[:min(2, len(paths))]  # 安全地选择前两个
        )

        # 存储每个路径选择的方法
        path_methods = {}

        # 为每个选中的路径显示方法选择器
        for path in selected_paths:
            methods = [m.upper() for m in paths[path].keys() if m.lower() in ['get', 'post', 'put', 'patch', 'delete']]
            if methods:
                selected_methods = st.multiselect(
                    f"选择 {path} 的方法:",
                    options=methods,
                    default=methods,
                    key=f"methods_{path}"
                )
                path_methods[path] = [m.lower() for m in selected_methods]

        # 使用一个按钮并检查条件
        generate_clicked = st.button("生成新 API Schema", key="generate_button")

        if generate_clicked:
            if not path_methods:
                st.warning("请至少选择一个路径和方法")
            else:
                new_schema = {
                    "openapi": schema_data.get("openapi", "3.0.0"),
                    "info": schema_data.get("info", {"title": "Generated API", "version": "1.0.0"}),
                    "paths": {}
                }

                # 添加选中的路径和方法
                for path, methods in path_methods.items():
                    new_schema["paths"][path] = {}
                    for method in methods:
                        if method in paths[path]:
                            new_schema["paths"][path][method] = paths[path][method]

                # 查找所有引用的 schemas
                referenced_schemas = find_referenced_schemas(new_schema["paths"])

                # 添加组件部分（只包含引用的 schemas）
                if "components" in schema_data and referenced_schemas:
                    new_components = {"schemas": {}}

                    # 只添加被引用的 schemas
                    for schema_name in referenced_schemas:
                        if schema_name in schema_data["components"]["schemas"]:
                            new_components["schemas"][schema_name] = schema_data["components"]["schemas"][schema_name]

                    # 添加 securitySchemes（如果存在）
                    if "securitySchemes" in schema_data["components"]:
                        new_components["securitySchemes"] = schema_data["components"]["securitySchemes"]

                    new_schema["components"] = new_components

                try:
                    # 生成 YAML 内容
                    yaml_content = yaml.dump(new_schema, sort_keys=False, allow_unicode=True, width=120)

                    # 保存到文件
                    file_path = Path("api_schema.yaml")
                    with file_path.open("w", encoding="utf-8") as f:
                        f.write(yaml_content)

                    st.success(f"文件已保存至: {file_path.absolute()}")

                    # 显示YAML内容在可折叠区域
                    with st.expander("查看生成的YAML内容"):
                        st.code(yaml_content, language="yaml")

                    # 提供下载按钮
                    st.download_button(
                        label="下载 YAML 文件",
                        data=yaml_content,
                        file_name="api_schema.yaml",
                        mime="application/yaml",
                        key="download_button"
                    )

                    # 显示精简信息
                    st.info(
                        f"精简后的组件: 包含 {len(referenced_schemas)} 个 schemas (原 {len(schema_data.get('components', {}).get('schemas', {}))} 个)")
                except Exception as e:
                    st.error(f"生成YAML文件时出错: {str(e)}")
else:
    st.warning("无法加载 OpenAPI schema，请确保 API 服务正在运行")

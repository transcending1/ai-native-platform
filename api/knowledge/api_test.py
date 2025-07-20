import requests
import unittest

# # API 基础配置
# BASE_URL = "http://localhost:8000/api"
# HEADERS = {"Content-Type": "application/json"}
BASE_URL = "http://localhost:8000/api"
AUTH_TOKEN = "7000681fbe8b77553aa419bad5c96c5e56528eec"  # 替换为实际Token
HEADERS = {
    "Authorization": f"Token {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


class NoteAppAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """创建测试数据"""
        # 创建命名空间
        namespace_data = {"name": "test_namespace", "description": "API测试空间"}
        response = requests.post(f"{BASE_URL}/namespaces/", json=namespace_data, headers=HEADERS)
        cls.namespace = response.json()

        # 创建根目录
        root_dir_data = {
            "name": "root_dir",
            "namespace": cls.namespace["id"],
            "parent": None
        }
        response = requests.post(f"{BASE_URL}/directories/", json=root_dir_data, headers=HEADERS)
        cls.root_dir = response.json()

        # 创建子目录
        child_dir_data = {
            "name": "child_dir",
            "namespace": cls.namespace["id"],
            "parent": cls.root_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/directories/", json=child_dir_data, headers=HEADERS)
        cls.child_dir = response.json()

        # 创建笔记
        note_data = {
            "title": "test_note",
            "content": "## 测试内容",
            "directory": cls.child_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/notes/", json=note_data, headers=HEADERS)
        cls.note = response.json()

    @classmethod
    def tearDownClass(cls):
        """清理测试数据"""
        requests.delete(f"{BASE_URL}/namespaces/{cls.namespace['id']}/")

    def test_1_namespace_operations(self):
        """测试命名空间CRUD操作"""
        # 创建新命名空间
        data = {"name": "temp_namespace", "description": "临时空间"}
        response = requests.post(f"{BASE_URL}/namespaces/", json=data, headers=HEADERS)
        self.assertEqual(response.status_code, 201)
        namespace_id = response.json()["id"]

        # 获取命名空间
        response = requests.get(f"{BASE_URL}/namespaces/{namespace_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "temp_namespace")

        # 更新命名空间
        update_data = {"description": "更新描述"}
        response = requests.patch(
            f"{BASE_URL}/namespaces/{namespace_id}/",
            json=update_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["description"], "更新描述")

        # 删除命名空间
        response = requests.delete(f"{BASE_URL}/namespaces/{namespace_id}/")
        self.assertEqual(response.status_code, 204)

        # 验证删除
        response = requests.get(f"{BASE_URL}/namespaces/{namespace_id}/")
        self.assertEqual(response.status_code, 404)

    def test_2_directory_operations(self):
        """测试目录CRUD操作"""
        # 创建新目录
        data = {
            "name": "new_dir",
            "namespace": self.namespace["id"],
            "parent": self.root_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/directories/", json=data, headers=HEADERS)
        self.assertEqual(response.status_code, 201)
        dir_id = response.json()["id"]

        # 获取目录
        response = requests.get(f"{BASE_URL}/directories/{dir_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "new_dir")

        # 更新目录
        update_data = {"name": "updated_dir",
                       "namespace": self.namespace["id"],
                       "parent": self.root_dir["id"]}
        response = requests.patch(
            f"{BASE_URL}/directories/{dir_id}/",
            json=update_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "updated_dir")

        # 测试唯一性约束
        duplicate_data = {
            "name": "child_dir",  # 与现有目录同名
            "namespace": self.namespace["id"],
            "parent": self.root_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/directories/", json=duplicate_data, headers=HEADERS)
        self.assertEqual(response.status_code, 400)
        self.assertIn("The fields namespace, parent, name must make a unique set.",
                      response.json()["non_field_errors"][0])

        # 删除目录
        response = requests.delete(f"{BASE_URL}/directories/{dir_id}/")
        self.assertEqual(response.status_code, 204)

    def test_3_note_operations(self):
        """测试笔记CRUD操作"""
        # 创建新笔记
        data = {
            "title": "new_note",
            "content": "新笔记内容",
            "directory": self.child_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/notes/", json=data, headers=HEADERS)
        self.assertEqual(response.status_code, 201)
        note_id = response.json()["id"]

        # 获取笔记
        response = requests.get(f"{BASE_URL}/notes/{note_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "new_note")

        # 更新笔记
        update_data = {"title": "updated_note", "content": "更新后的内容", "directory": self.child_dir["id"]}
        response = requests.patch(
            f"{BASE_URL}/notes/{note_id}/",
            json=update_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "updated_note")

        # 测试唯一性约束
        duplicate_data = {
            "title": "test_note",  # 与现有笔记同名
            "content": "重复标题",
            "directory": self.child_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/notes/", json=duplicate_data, headers=HEADERS)
        self.assertEqual(response.status_code, 400)
        self.assertIn("The fields directory, title must make a unique set.", response.json()["non_field_errors"][0])

        # 删除笔记
        response = requests.delete(f"{BASE_URL}/notes/{note_id}/")
        self.assertEqual(response.status_code, 204)

    def test_4_directory_tree(self):
        """测试目录树接口"""
        response = requests.get(
            f"{BASE_URL}/directories/tree/{self.namespace['id']}/",
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)
        tree_data = response.json()

        # 验证树结构
        self.assertEqual(len(tree_data), 1)  # 应有一个根目录
        root = tree_data[0]
        self.assertEqual(root["name"], "root_dir")
        self.assertEqual(len(root["children"]), 1)  # 应有一个子目录

        child = root["children"][0]
        self.assertEqual(child["name"], "child_dir")
        self.assertEqual(len(child["notes"]), 1)  # 应有一个笔记

        note = child["notes"][0]
        self.assertEqual(note["title"], "test_note")

    def test_5_move_directory(self):
        """测试移动目录"""
        # ... 前面的测试代码不变 ...

        # 测试循环引用 - 尝试移动到自己的后代
        grandchild_data = {
            "name": "grandchild",
            "namespace": self.namespace["id"],
            "parent": self.child_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/directories/", json=grandchild_data, headers=HEADERS)
        grandchild_dir = response.json()

        # 尝试将根目录移动到孙子目录
        invalid_data = {"parent_id": grandchild_dir["id"]}
        response = requests.post(
            f"{BASE_URL}/directories/{self.root_dir['id']}/move/",
            json=invalid_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("不能移动到子目录中", response.json()["error"])

        # 测试移动到自身
        self_invalid_data = {"parent_id": self.root_dir["id"]}
        response = requests.post(
            f"{BASE_URL}/directories/{self.root_dir['id']}/move/",
            json=self_invalid_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("不能移动到自身", response.json()["error"])

        # 清理
        requests.delete(f"{BASE_URL}/directories/{grandchild_dir['id']}/")

    def test_6_move_note(self):
        """测试移动笔记"""
        # 创建目标目录
        target_data = {
            "name": "note_target",
            "namespace": self.namespace["id"],
            "parent": self.root_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/directories/", json=target_data, headers=HEADERS)
        target_dir = response.json()

        # 1. 正常移动测试
        move_data = {"directory_id": target_dir["id"]}
        response = requests.post(
            f"{BASE_URL}/notes/{self.note['id']}/move/",
            json=move_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["directory"], target_dir["id"])

        # 2. 测试同名笔记冲突 - 修正逻辑
        # 先移回原目录以便创建冲突笔记
        move_back_data = {"directory_id": self.child_dir["id"]}
        response = requests.post(
            f"{BASE_URL}/notes/{self.note['id']}/move/",
            json=move_back_data,
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)

        # 在目标目录创建同名笔记
        conflict_note_data = {
            "title": self.note["title"],
            "content": "冲突内容",
            "directory": target_dir["id"]
        }
        response = requests.post(f"{BASE_URL}/notes/", json=conflict_note_data, headers=HEADERS)
        self.assertEqual(response.status_code, 201)  # 应该成功创建
        conflict_note = response.json()

        # 尝试移动笔记到有同名笔记的目录
        response = requests.post(
            f"{BASE_URL}/notes/{self.note['id']}/move/",
            json={"directory_id": target_dir["id"]},
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("目标目录已存在同名笔记", response.json()["error"])

        # 3. 测试跨命名空间移动
        other_namespace = requests.post(
            f"{BASE_URL}/namespaces/",
            json={"name": "other_ns"},
            headers=HEADERS
        ).json()
        other_dir = requests.post(
            f"{BASE_URL}/directories/",
            json={
                "name": "other_dir",
                "namespace": other_namespace["id"],
                "parent": None
            },
            headers=HEADERS
        ).json()

        response = requests.post(
            f"{BASE_URL}/notes/{self.note['id']}/move/",
            json={"directory_id": other_dir["id"]},
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("不能跨命名空间移动笔记", response.json()["error"])

        # 4. 测试移动到自身目录（应该允许）
        response = requests.post(
            f"{BASE_URL}/notes/{self.note['id']}/move/",
            json={"directory_id": self.child_dir["id"]},
            headers=HEADERS
        )
        self.assertEqual(response.status_code, 200)

        # 5. 清理
        requests.delete(f"{BASE_URL}/notes/{conflict_note['id']}/", headers=HEADERS)
        requests.delete(f"{BASE_URL}/directories/{target_dir['id']}/", headers=HEADERS)
        requests.delete(f"{BASE_URL}/namespaces/{other_namespace['id']}/", headers=HEADERS)


if __name__ == "__main__":
    unittest.main()

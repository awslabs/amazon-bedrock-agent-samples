import unittest

from InlineAgent.knowledge_base import KnowledgeBasePlugin as KnowledgeBase


class TestKnowledgeBase(unittest.TestCase):
    def test___init___1(self):
        knowledgeBases = [
            {"description": "MOCK_1", "name": "SKaEdphpZh"},
            {"description": "MOCK_2", "name": "SKaEdphpZh"},
        ]

        for knowledgeBase in knowledgeBases:
            knowledge_base_schema = KnowledgeBase(**knowledgeBase).to_dict()

            self.assertEqual(
                knowledge_base_schema["description"], knowledgeBase["description"]
            )
            self.assertEqual(
                knowledge_base_schema["knowledgeBaseId"],
                "ThisIsMockId",
            )

    def test___init___2(self):
        knowledgeBases = [{"name": "MOCK_1"}, {"description": "MOCK_2"}]

        idx = 0
        for knowledgeBase in knowledgeBases:
            error = str()
            try:
                _ = KnowledgeBase(**knowledgeBase).to_dict()
            except Exception as e:
                error = str(e)

            if idx == 0:

                self.assertNotIn(
                    "TypeError: KnowledgeBase.__init__() missing 1 required positional argument: 'description'",
                    error,
                )
            elif idx == 1:
                self.assertNotIn(
                    "TypeError: KnowledgeBase.__init__() missing 1 required positional argument: 'knowledgeBaseId'",
                    error,
                )
            else:
                self.fail()

            idx += 1

    def test___init___3(self):
        knowledgeBases = [
            {"description": "MOCK_1", "name": "SKaEdphpZh"},
            {
                "description": "MOCK_2",
                "name": "SKaEdphpZh",
                "additional_props": {
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "filter": {
                                "andAll": [
                                    {
                                        "equals": {
                                            "key": "employee_name",
                                            "value": "Alex Anderson",
                                        }
                                    },
                                    {
                                        "equals": {
                                            "key": "document_type",
                                            "value": "finance",
                                        }
                                    },
                                ]
                            }
                        }
                    },
                },
            },
        ]
        idx = 0
        for knowledgeBase in knowledgeBases:
            knowledge_base_schema = KnowledgeBase(**knowledgeBase).to_dict()
            self.assertEqual(
                knowledge_base_schema["description"], knowledgeBase["description"]
            )
            self.assertEqual(
                knowledge_base_schema["knowledgeBaseId"],
                "ThisIsMockId",
            )
            if idx == 1:
                self.assertEqual(
                    knowledge_base_schema["retrievalConfiguration"],
                    knowledgeBase["additional_props"]["retrievalConfiguration"],
                )
            idx += 1


if __name__ == "__main__":
    unittest.main()

"""测试配置管理"""

from src.config import settings


class TestSettings:
    """验证 Settings 类正确加载"""

    def test_default_values(self):
        """默认值正确"""
        assert settings.APP_NAME == "Smart Doc Analyzer"
        assert settings.EMBEDDING_DIM == 1024
        assert settings.CHUNK_SIZE == 500

    def test_types(self):
        """字段类型正确"""
        assert isinstance(settings.DEBUG, bool)
        assert isinstance(settings.QDRANT_PORT, int)
        assert isinstance(settings.RETRIEVAL_TOP_K, int)
        assert isinstance(settings.MAX_UPLOAD_SIZE_MB, int)

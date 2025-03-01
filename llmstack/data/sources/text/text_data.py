import base64
import logging
import uuid

from llmstack.data.sources.base import BaseSource, DataDocument
from llmstack.data.sources.utils import create_source_document_asset

logger = logging.getLogger(__file__)

"""
Entry configuration schema for text data source type
"""


class TextSchema(BaseSource):
    name: str = "Untitled"
    content: str = ""

    @classmethod
    def slug(cls):
        return "text"

    @classmethod
    def provider_slug(cls):
        return "promptly"

    def get_data_documents(self, **kwargs):
        id = str(uuid.uuid4())
        data_uri = f"data:text/plain;name={self.name}.txt;base64,{base64.b64encode(self.content.encode('utf-8')).decode('utf-8')}"
        file_objref = create_source_document_asset(
            data_uri, datasource_uuid=kwargs.get("datasource_uuid", None), document_id=id
        )

        return [
            DataDocument(
                id_=id,
                name=self.name,
                content=file_objref,
                text=self.content,
                text_objref=file_objref,
                mimetype="text/plain",
                metadata={"source": self.name, "mime_type": "text/plain"},
                datasource_uuid=kwargs["datasource_uuid"],
            )
        ]

    @classmethod
    def process_document(cls, document: DataDocument) -> DataDocument:
        from llmstack.assets.utils import get_asset_by_objref

        datasource_uuid = document.datasource_uuid
        file_asset = get_asset_by_objref(document.content, None, datasource_uuid)
        text = file_asset.file.read().decode("utf-8")

        return document.model_copy(update={"text": text})

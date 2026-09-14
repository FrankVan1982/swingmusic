"""
Contains the classical music routes.
"""

from flask_openapi3 import Tag
from flask_openapi3 import APIBlueprint
from pydantic import BaseModel, Field

from swingmusic.config import UserConfig
from swingmusic.premium import ClassicalStore, CloudError, LicenseError

bp_tag = Tag(name="Classical", description="Classical works")
api = APIBlueprint("classical", __name__, url_prefix="/classical", abp_tags=[bp_tag])


class GetWorkPath(BaseModel):
    token: str = Field(
        description="A workhash or a catalogue id hash (catalogue_ids[].hash)",
    )


class GetWorkQuery(BaseModel):
    albumhash: str = Field(
        description="Focus the recording from this album (defaults to the recording with the most tracks)",
        default="",
    )


@api.get("/work/<token>")
def get_work(path: GetWorkPath, query: GetWorkQuery):
    """
    Get a classical work

    Returns the work's display data, the movements of the focused recording,
    and album cards for its other recordings. Resolves by workhash or by any
    of the work's catalogue id hashes (which survive re-indexing).

    Responds 404 when classical support is unavailable.
    """
    if ClassicalStore is None or not UserConfig().classicalEnabled:
        return {"msg": "Work not found"}, 404

    try:
        work = ClassicalStore.get_work(path.token) or (
            ClassicalStore.get_work_by_catalogue_id(path.token)
        )

        if work is None:
            return {"msg": "Work not found"}, 404

        from swingmusic.premium.classical.serializers import serialize_work

        payload = serialize_work(work.workhash, albumhash=query.albumhash or None)

        if payload is None:
            return {"msg": "Work not found"}, 404

        return payload, 200
    except (LicenseError, CloudError, ImportError) as e:
        print("error serializing work", e)
        return {"msg": "Work not found"}, 404

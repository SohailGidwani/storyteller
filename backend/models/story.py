from typing import Literal, Union
from pydantic import BaseModel


class TextBlock(BaseModel):
    type: Literal["text"]
    content: str


class ImageSlot(BaseModel):
    type: Literal["image_slot"]
    prompt: str
    alt: str
    image_url: str | None = None


class ClickableEntity(BaseModel):
    entity_id: str
    word_in_text: str
    name: str
    type: Literal["character", "location", "object", "creature"]
    lore: str
    image_prompt: str
    image_url: str | None = None
    questions: list[str]


class SceneNavigation(BaseModel):
    next_scene_id: str | None


class Scene(BaseModel):
    scene_id: str
    act: int
    act_name: str
    title: str
    text_blocks: list[Union[TextBlock, ImageSlot]]
    clickable_entities: list[ClickableEntity]
    navigation: SceneNavigation


class StoryJSON(BaseModel):
    story_id: str
    status: Literal["complete", "generating", "failed"]
    photo_url: str
    title: str
    child_name: str
    age_band: Literal["4-5", "6-8", "9+"]
    act_structure: Literal["3_act", "5_act", "7_act"]
    story_type: str
    scenes: list[Scene]


class GenerateRequest(BaseModel):
    child_name: str
    age: int
    photo_url: str
    story_type: Literal[
        "fantasy_adventure",
        "space_explorer",
        "animal_quest",
        "superhero_mission",
        "royal_tale",
    ]
    gender: Literal["boy", "girl"] = "girl"
    adhd: bool = False


class GenerateResponse(BaseModel):
    story_id: str
    status: Literal["complete", "generating", "failed"]
    story: StoryJSON | None = None

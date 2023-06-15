from typing import List,Optional,Any
from pydantic import BaseModel

class TwitterUrls(BaseModel):
    url                                 :str
    expanded_url                        :str
    display_url                         :str
    indices                             :List[int]

class TwitterUserEntitiesUrl(BaseModel):
    urls                                :List[TwitterUrls]

class TwitterUserEntities(BaseModel):
    url                                 :TwitterUserEntitiesUrl
    description                         :TwitterUserEntitiesUrl

class TwitterUser(BaseModel):
    id                                  :int
    id_str                              :str
    name                                :str
    screen_name                         :str
    location                            :str
    description                         :str
    url                                 :str
    entities                            :TwitterUserEntities
    protected                           :bool
    followers_count                     :int
    friends_count                       :int
    listed_count                        :int
    created_at                          :str
    favourites_count                    :int
    utc_offset                          :Optional[str]
    time_zone                           :Optional[str]
    geo_enabled                         :bool
    verified                            :bool
    statuses_count                      :int
    lang                                :Optional[str]
    contributors_enabled                :bool
    is_translator                       :bool
    is_translation_enabled              :bool
    profile_background_color            :str 
    profile_background_image_url        :str
    profile_background_image_url_https  :str
    profile_background_tile             :bool
    profile_image_url                   :str
    profile_image_url_https             :str
    profile_banner_url                  :str
    profile_link_color                  :str
    profile_sidebar_border_color        :str
    profile_sidebar_fill_color          :str
    profile_text_color                  :str
    profile_use_background_image        :bool
    has_extended_profile                :bool
    default_profile                     :bool
    default_profile_image               :bool
    following                           :Optional[str] 
    follow_request_sent                 :Optional[str] 
    notifications                       :Optional[str]
    translator_type                     :str 
    withheld_in_countries               :List[Any]



class TwitterMetadata(BaseModel):
    iso_language_code                   :str
    result_type                         :str



class TwitterEntities(BaseModel):
    hashtags                            :List[str]
    symbols                             :List[str]
    user_mentions                       :List[str]
    urls                                :List[TwitterUrls]

class TwitterTweet(BaseModel):
    create_at                           :Optional[str]
    id                                  :int
    id_str                              :str
    text                                :str
    truncated                           :bool
    entities                            :TwitterEntities
    metadata                            :TwitterMetadata
    source                              :str
    in_reply_to_status_id               :Optional[int]
    in_reply_to_user_id                 :Optional[int]
    in_reply_to_status_id_str           :Optional[str]
    in_reply_to_user_id_str             :Optional[str]
    in_reply_to_screen_name             :Optional[str]
    user                                :TwitterUser
    geo                                 :Optional[Any]
    coordinates                         :Optional[Any] 
    place                               :Optional[Any]
    contributors                        :Optional[Any]
    is_quote_status                     :bool
    retweet_count                       :int
    favorite_count                      :int 
    favorited                           :bool
    retweeted                           :bool
    lang                                :str
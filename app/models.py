from app.database import BaseModel
import peewee as pw
from datetime import datetime

class User(BaseModel):
    """User model for Cartoon Orbit users — authenticated via Discord"""
    discord_id = pw.CharField(unique=True, max_length=30)
    discord_username = pw.CharField(max_length=100)
    username = pw.CharField(unique=True, max_length=50, null=True)
    avatar = pw.CharField(max_length=100, null=True)
    points = pw.IntegerField(default=100)
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    last_login = pw.DateTimeField(null=True)
    is_active = pw.BooleanField(default=True)
    is_admin = pw.BooleanField(default=False)
    last_ip = pw.CharField(max_length=45, null=True)

    class Meta:
        table_name = 'users'

class CToon(BaseModel):
    """cToon model - the collectible cards"""
    name = pw.CharField(max_length=100)
    description = pw.TextField(null=True)
    image_url = pw.CharField(max_length=255)
    rarity = pw.CharField(max_length=20, default='common')
    created_at = pw.DateTimeField(default=datetime.now)
    mint_count = pw.IntegerField(default=0)
    ctoon_set = pw.CharField(max_length=100, null=True)
    series = pw.CharField(max_length=100, null=True)
    release_date = pw.DateTimeField(null=True)
    cmart_value = pw.IntegerField(default=0)
    edition = pw.IntegerField(default=1)
    deletable = pw.BooleanField(default=False)
    minted = pw.IntegerField(default=0)
    in_cmart = pw.BooleanField(default=False)

    class Meta:
        table_name = 'ctoons'

class UserCToon(BaseModel):
    """User's collection of cToons — each row is one unique minted copy"""
    user = pw.ForeignKeyField(User, backref='ctoons')
    ctoon = pw.ForeignKeyField(CToon, backref='owners')
    mint_number = pw.IntegerField()
    acquired_at = pw.DateTimeField(default=datetime.now)
    acquired_via = pw.CharField(max_length=20, default='cmart')  # cmart, code, prize

    class Meta:
        table_name = 'user_ctoons'
        indexes = (
            (('ctoon', 'mint_number'), True),  # Each minted copy is unique globally
        )

class CZone(BaseModel):
    """User's personal gallery space"""
    user = pw.ForeignKeyField(User, backref='czone')
    name = pw.CharField(max_length=100, default='My cZone')
    background_url = pw.CharField(max_length=255, null=True)
    description = pw.TextField(null=True)
    is_public = pw.BooleanField(default=True)
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'czones'

class CZoneItem(BaseModel):
    """Items placed in a cZone"""
    czone = pw.ForeignKeyField(CZone, backref='items')
    ctoon = pw.ForeignKeyField(CToon, backref='czone_placements')
    position_x = pw.IntegerField(default=0)
    position_y = pw.IntegerField(default=0)
    z_index = pw.IntegerField(default=1)
    placed_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'czone_items'


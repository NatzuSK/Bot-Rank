import nextcord,json,pymongo
import random
from nextcord.ext import commands


bot = commands.Bot(intents=nextcord.Intents.all())
config = json.load(open("config/config.json","r"))




myclient = pymongo.MongoClient(config['mongodb'])
mydb = myclient["level"]
mycol = mydb["user"]







def search(user_id):
    return mycol.find_one({"id": user_id}) is not None




def point():
    point =  random.randint(10,15)
    return point





@bot.event
async def on_ready():
    print(f"{bot.user.name} Is online!")




def level(points):
    level_point = [100, 250, 500, 1000 ,2000]
    level = 0
    for threshold in level_point:
        if points >= threshold:
            level += 1
    if level > len(level_point):
        return "MAX"
    return level


@bot.slash_command(name="rank", description="ตรวจสอบเลเวลของตัวเอง")
async def rank(ctx: nextcord.Interaction):
    user_id = str(ctx.user.id)  
    user_data = mycol.find_one({"id": user_id}) 

    if user_data:
        user_point = user_data["point"]
        user_level = level(user_point)


        all_users = list(mycol.find().sort("point", -1))
        rank_position = [i for i, u in enumerate(all_users, start=1) if u["id"] == user_id][0]


        if user_level == "MAX":
            embed = nextcord.Embed(
                color=nextcord.Color.blue(),
                description=f"""
                **Stats on server {ctx.guild.name}**

                **👤  {ctx.user}**
                ✨  Total XP: `{user_point}` คะแนน  
                ✨  Level: `{user_level}`   
                🎉  Next Lv: `{user_level + 1}` 
                🏆  Rank: `{rank_position}`
                """
            )
        else:
            embed = nextcord.Embed(
                
                color=nextcord.Color.blue(),
                description=f"""
                **Stats on server {ctx.guild.name}**

                **👤  {ctx.user}**
                ✨  Total XP: `{user_point}` point  
                ✨  Level: `{user_level}`   
                🎉  Next Lv: `{user_level + 1}` 
                🏆  Rank: `{rank_position}`
                """
                
                
            )
        embed.set_thumbnail(url=ctx.user.display_avatar.url)

        if int(ctx.guild.id) == int(config["server"]["id"]): 
            await ctx.response.send_message(
                ephemeral=True,
                
                embed=embed
            )
        else:
            await ctx.response.send_message(
                ephemeral=True,
                content="คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์ที่กำหนด"
            )
    else:
        await ctx.response.send_message(
            ephemeral=True,
            content="ไม่พบข้อมูลผู้ใช้ในฐานข้อมูล"
        )





@bot.slash_command(name="admin_point", description="เพิ่มpoint(สำหรับแอดมิน)")
async def admin_point(ctx: nextcord.Interaction, member: nextcord.User, points: int):
    if (int(ctx.guild.id) == int(config["server"]["id"])):
        if ctx.user.guild_permissions.administrator:
            user_id = str(member.id)
            if search(user_id):
                mycol.update_one(
                    {"id": user_id},
                    {"$set": {"point": points}}
                )
                await ctx.response.send_message(f"```✅ คะแนนของ {member.name} ถูกแก้ไขเป็น {points} คะแนน```", ephemeral=True)
            else:
                 await ctx.response.send_message(f"❌ ไม่พบข้อมูลผู้ใช้ {member.name} ในฐานข้อมูล", ephemeral=True)





@bot.slash_command(name="top", description="ตรวจสอบลำดับ")
async def top(ctx: nextcord.Interaction):

    top_users = mycol.find().sort("point", pymongo.DESCENDING).limit(10)
    
    embed = nextcord.Embed(
        title="🏆 **Top 10 Players** 🏆",
        description="ตรวจสอบอันดับผู้ใช้ที่มีคะแนนสูงสุดในเซิร์ฟเวอร์\n\n",
        color=nextcord.Color.blue(),
    )
    

    
    rank = 1
    for user in top_users:
        embed.add_field(
            name=f"**🏆 อันดับ {rank}**",
            value=f"**👤 ผู้ใช้**: <@{user['id']}>\n**คะแนน**: `{user['point']}`\n",
            inline=False
        )
        rank += 1
    
    await ctx.response.send_message(embed=embed, ephemeral=True)



@bot.event
async def on_message(message):
    if message.guild is None:
        return

    if (int(message.guild.id) == int(config["server"]["id"])) and (int(config["server"]["ch"]) == int(message.channel.id)):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        if search(user_id):
            user_data = mycol.find_one({"id": user_id})
            new_point  = user_data.get("point") + point()

            mycol.update_one(
                {"id": user_id},
                {"$set": {"point": new_point}}
            )

            old_level = level(user_data.get("point"))
            new_level = level(new_point)

            if new_level > old_level:
                embed = nextcord.Embed(
                    title="**ยินดีด้วย!**",
                    description=f"```🎉คุณเลเวลอัปเป็นเลเวล {new_level} แล้ว!```",
                    color=nextcord.Color.blue()
                )
                try:
                    await message.author.send(embed=embed)
                except nextcord.Forbidden:
                    print(f"❌ ไม่สามารถส่ง DM ไปยัง {message.author} ได้")

        else:
            mycol.insert_one({"id": user_id, "point": 0})












bot.run(config["token"])






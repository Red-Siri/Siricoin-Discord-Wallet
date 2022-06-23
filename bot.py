#Coin config
node_URL = "https://node-1.siricoin.tech:5006"

explorer = 'https://explorer.siricoin.tech/transaction.html?hash='

Cointicker = 'Siri'
CoinName = 'Siricoin'
BlockReward = 50

Contact = "@The Red Eye Studio#8319"

HelpURL = "https://github.com/Red-Siri/Siricoin-Discord-Wallet/wiki/Commands"
gitrepo = "https://github.com/Red-Siri/Siricoin-Discord-Wallet"




#ADVANCED SECTION, you may keep this as is

prefix = '/'
Creator = "[the-red-eye-studio](https://github.com/the-red-eye-studio/)"

#Imports
from termcolor import colored
from discord.ext import commands
from discord_slash import SlashCommand
from firebase_admin import credentials, firestore
from eth_account import Account
from siricoin import siriCoin
from Web3Decode import DecodeRawTX
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import (
    ComponentContext,
    create_actionrow,
    create_button,
)
import requests, discord, os, pyotp, firebase_admin, qrcode, secrets, json


#FireStore collections, no need to change this
Collection='2FA'
tempCollection='temp_2FA'

Keys_Collection = "Keys"
idToKey_Collection = "id-addr"
KeyToAddr_Collection = "addr-id"


#Discord auth token
DiscordToken = open("DiscordToken", "r").read()


# QR code config
qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5)

#Bot stuff
bot = commands.Bot(command_prefix=prefix)
embed=discord.Embed()
slash=SlashCommand(bot, sync_commands=True)

#fireStore stuff
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#Siri config
siri = siriCoin(node_URL)

#Just a header, no need to change this
headers = {
    'content-type': 'text/plain;',
}

def getUser(addr):
    doc_ref = db.collection(KeyToAddr_Collection).document(addr)
    doc = doc_ref.get()

    if doc.exists:
        dt = requests.post('https://lookupguru.herokuapp.com/lookup', json={'input': doc.to_dict()["id"]}).json()["data"]
        return dt["username"] + "#" + str(dt["discriminator"])
    else:
        return addr

def getAddr(id):
    doc_ref = db.collection(idToKey_Collection).document(str(id))
    doc = doc_ref.get()

    if doc.exists:
        dt = requests.post('https://lookupguru.herokuapp.com/lookup', json={'input': str(id)}).json()["data"]
        return doc.to_dict()["addr"], dt["username"] + "#" + str(dt["discriminator"]), dt["avatar"]["url"]

    else:
        return None


def CreateWallet(id):
    WalletName = str(id)

    doc_ref = db.collection(Keys_Collection).document(WalletName)
    doc = doc_ref.get()

    if doc.exists:
        return None

    if not doc.exists:
        priv = "0x" + secrets.token_hex(32)
        addr = Account.from_key(priv).address
        doc_ref.set({
            'address': addr,
            'privKey': priv
        })

        db.collection(KeyToAddr_Collection).document(addr).set({
            'id':str(WalletName)
        })

        db.collection(idToKey_Collection).document(WalletName).set({
            'addr':addr
        })

        return True




@bot.event
async def on_ready():
    print(colored('We have logged in as {0.user}'.format(bot), "green"))

@slash.slash(description="help message")
async def help(ctx):
    embed.add_field(name="Maintained by: ", value=Contact, inline=False)
    embed.add_field(name="Created by: ", value=Creator, inline=False)
    actionrow = create_actionrow(
        *[
            create_button(
                label="Command documentation", url=HelpURL, style=ButtonStyle.URL
            ),
            create_button(
                label="Github repository", url=gitrepo, style=ButtonStyle.URL
            )
        ]
    )

    await ctx.send(embed=embed, components=[actionrow])
    embed.clear_fields()

# wallet balance
@slash.slash(description="shows a users balance")
async def balance(ctx, member=""):
    await ctx.defer()

    embed.clear_fields()
    embed.remove_author()
    Continue = True
    if not member=="":
        try:
            id = int(str(member).replace("<@!", "").replace(">", ""))
        except:
            Continue = False
            embed.add_field(name='Error ❌', value='User not found, please use @UserName on the ``member`` parameter')
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
    else:
        id = ctx.author.id

    if Continue:
        Continue = False
        gAddr = getAddr(id)

        if not gAddr == None:
            addr = gAddr[0]
            uname = gAddr[1]
            avatar = gAddr[2]
            Continue = True
        else:
            WalletName = str(id)
            doc_ref = db.collection(idToKey_Collection).document(WalletName)
            doc = doc_ref.get()
            if doc.exists:
                addr = doc.to_dict()["addr"]
                Continue = True
            uname = ctx.author
            avatar = (ctx.author).avatar_url

        if Continue:
            embed.add_field(name='Balance is:', value=str(float(siri.balance(addr))) + str(" ") +  str(CoinName))
            embed.set_author(name=str(uname) + "'s", icon_url=avatar)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()

        if not Continue:
            if CreateWallet(id) == True:
                embed.add_field(name="Error ❌", value="My bad, please run the command again")
                embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
                await ctx.reply(embed=embed)
                embed.clear_fields()
                embed.remove_author()


    WalletName = ""
    embed.clear_fields()
    embed.remove_author()

# get a users address
@slash.slash(description='get a users address')
async def address(ctx, member=""):
    await ctx.defer()

    embed.clear_fields()
    embed.remove_author()

    Continue = True
    if not member=="":
        try:
            id = int(str(member).replace("<@!", "").replace(">", ""))
        except:
            Continue = False
            embed.add_field(name='Error ❌', value='User not found, please use @UserName on the ``member`` parameter')
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
    else:
        id = ctx.author.id

    if Continue:
        Continue = False
        gAddr = getAddr(id)
        if not gAddr == None:
            addr = gAddr[0]
            uname = gAddr[1]
            avatar = gAddr[2]
            Continue = True
        else:
            WalletName = str(id)
            doc_ref = db.collection(idToKey_Collection).document(WalletName)
            doc = doc_ref.get()
            if doc.exists:
                addr = doc.to_dict()["addr"]
                Continue = True
            uname = ctx.author
            avatar = (ctx.author).avatar_url

        if Continue:
            embed.add_field(name='Address is:', value= "``" + addr + "``")
            embed.set_author(name=str(uname) + "'s", icon_url=avatar)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()


        if not Continue:
            if CreateWallet(id) == True:
                embed.add_field(name="Error ❌", value="My bad, please run the command again")
                embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
                await ctx.reply(embed=embed)
                embed.clear_fields()
                embed.remove_author()


    WalletName = ""
    embed.clear_fields()
    embed.remove_author()


# list transactions
@slash.slash(description='list transactions')
async def list_transactions(ctx, tx_asked:int=4, member=""):
    await ctx.defer()

    embed.clear_fields()
    embed.remove_author()

    Continue = True
    MemberError = False
    if not member=="":
        try:
            id = int(str(member).replace("<@!", "").replace(">", ""))
        except:
            Continue = False
            MemberError = True
            embed.add_field(name='Error ❌', value='User not found, please use @UserName on the ``member`` parameter')
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
    else:
        id = ctx.author.id
    if Continue:
        Continue = False
        gAddr = getAddr(id)
        if not gAddr == None:
            addr = gAddr[0]
            uname = gAddr[1]
            avatar = gAddr[2]
            Continue = True
        else:
            WalletName = str(id)
            doc_ref = db.collection(idToKey_Collection).document(WalletName)
            doc = doc_ref.get()
            if doc.exists:
                addr = doc.to_dict()["addr"]
                Continue = True
            uname = ctx.author
            avatar = (ctx.author).avatar_url

    if Continue:

        ValueError=False
        if (tx_asked==0): await ctx.reply('https://tenor.com/view/house-explosion-explode-boom-kaboom-gif-19506150'); ValueError=True

        if not ValueError:
                response = requests.get(node_URL+"/accounts/accountInfo/" + addr)
                tx_s = json.loads(response.text)["result"]["transactions"]
                tx_s = tx_s[1:][::-1] # Remove first value (None) and then reverse the list
                embed.add_field(name="Transactions:", value='\n\u200b')

                if tx_asked > len(tx_s):
                    tx_asked = len(tx_s)

                for i in range (0, tx_asked):
                    response = requests.get(node_URL+"/get/transaction/" + tx_s[i])
                    tx = json.loads(json.loads(response.text)["result"]["data"])
                    if tx["type"] == 0:
                        if tx["to"] == addr:
                            embed.add_field(name="📈 Received " + str(float(tx["tokens"])) + str(" ") + str(Cointicker), value=(" **From:** ``" + getUser(tx["from"]) + str("``, [Explorer](" + explorer + str(json.loads(response.text)["result"]["hash"]) + str(")"))), inline=False)
                        else:
                            embed.add_field(name="📉 Sent: " + str(float(tx["tokens"])) + str(" ") + str(Cointicker) , value=(" **To:** ``" + getUser(tx["to"]) + str("``, [Explorer](" + explorer + str(json.loads(response.text)["result"]["hash"]) + str(")"))), inline=False)
                    if tx["type"] == 1:
                        embed.add_field(name="⛏️ Hit block", value=("Reward: " + str(float(BlockReward))  + ' ' + Cointicker + str(", [Explorer](" + explorer + str(json.loads(response.text)["result"]["hash"]) + str(")"))), inline=False)
                    if tx["type"] == 2:
                        w3_tx = DecodeRawTX(tx["rawTx"])
                        if w3_tx[1] == addr:
                            embed.add_field(name="📈 Received " + str(float(w3_tx[2])) + str(" ") + str(Cointicker), value=(" **From:** ``" + str(w3_tx[0]) + str("``, [Explorer](" + explorer + str(json.loads(response.text)["result"]["hash"]) + str(")"))), inline=False)
                        else:
                            embed.add_field(name="📉 Sent: " + str(float(w3_tx[2])) + str(" ") + str(Cointicker) , value=(" **To:** ``" + str(w3_tx[1]) + str("``, [Explorer](" + explorer + str(json.loads(response.text)["result"]["hash"]) + str(")"))), inline=False)


                embed.set_author(name=str(uname) + "'s", icon_url=avatar)
                try:
                    await ctx.reply(embed=embed)
                except:
                    embed.clear_fields()
                    embed.remove_author()
                    await (ctx.channel).send(ctx.author.mention + ", Please lower the ammount of TX's asked, if you need to see more transactions please use the Explorer https://explorer.siricoin.tech/address.html?address=" + addr)
    if not Continue and not MemberError:
        if CreateWallet(id) == True:
            embed.add_field(name="Error ❌", value="My bad, please run the command again")
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
    



    
#Enable 2FA
@slash.slash(description='enable 2fa')
async def enable2fa(ctx):
    await ctx.defer()

    embed.clear_fields()
    embed.remove_author()

    doc_ref = db.collection(Collection).document(str(ctx.author.id))
    doc = doc_ref.get()

    temp_doc_ref = db.collection(tempCollection).document(str(ctx.author.id))
    temp_doc = temp_doc_ref.get()

    if doc.exists:
        embed.add_field(name='...', value="Woah slow down there busta'! You can only enable 2FA once!")
        embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
        await ctx.reply(embed=embed)
        embed.clear_fields()
        embed.remove_author()

    if not doc.exists:
        base32secret = pyotp.random_base32()
        temp_doc_ref.set({
            u'base32Secret': base32secret,
            })
        embed.add_field(name='info ℹ', value='open your favorite authenticator app ready and open the QR code scanning tool, and scan this code. You may run it again if needed, once you scanned it run ``' + prefix + 'verify``' + 'to make the OTP reqiured on the ``' + prefix + "send`` command")
        embed.add_field(name='Warning ⚠', value='once you scanned the QR code and ran ``' + prefix + 'verify`` **please click dismiss message!**')
        embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
        await ctx.reply(embed=embed, hidden=True)
        embed.clear_fields()
        embed.remove_author()
        totp_uri = 'otpauth://totp/' + Cointicker + ' Discord Wallet?secret=' + base32secret
        #QR gen
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save('qrcode.png')
        qr.clear()
        #Send the QR code
        await ctx.reply(file=discord.File('qrcode.png'), hidden=True)
        os.remove("qrcode.png")

   

       
       
# verify 2FA
@slash.slash(description='Verify that you have setup 2FA successfully')
async def verify(ctx, otp_input:int):
    await ctx.defer()

    embed.clear_fields()
    embed.remove_author()

    doc_ref = db.collection(Collection).document(str(ctx.author.id))
    doc = doc_ref.get()

    temp_doc_ref = db.collection(tempCollection).document(str(ctx.author.id))
    temp_doc = temp_doc_ref.get()

    if doc.exists:
        totp = pyotp.TOTP(doc.to_dict()["base32Secret"])
        if int(totp.now())==int(otp_input):
            embed.add_field(name="I'm speachless...", value="Well... the OTP is correct, but you can't re-enable 2FA ¯\_(ツ)_/¯")
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
        else:
            embed.add_field(name='Dude...', value="The OTP is incorrect, and you can't re-enable 2FA ;-;")
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()

    if temp_doc.exists and not doc.exists:
        totp = pyotp.TOTP(temp_doc.to_dict()["base32Secret"])
        if int(totp.now())==int(otp_input):

            doc_ref.set({
            u'base32Secret': temp_doc.to_dict()["base32Secret"],
            })
            temp_doc_ref.delete()

            embed.add_field(name="Success!", value="The OTP was correct! You can now use it with the ``" + prefix +"send`` command👍" )
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
        else:
            embed.add_field(name='Dude...', value="The OTP was incorrect... Try again :grimacing:")
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
        
    if not temp_doc.exists and not doc.exists:
        embed.add_field(name='Error!', value="Please run ``" + prefix + "enable2fa`` first!")
        embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
        await ctx.reply(embed=embed)
        embed.clear_fields()
        embed.remove_author()




# send a transaction
@slash.slash(description='Send a Transaction')
async def send(ctx, amount, to_, otp_input=0):
    await ctx.defer()

    embed.clear_fields()
    embed.remove_author()

    continue_ = True 
    MemberError = False

    if not str(to_).startswith("0x"):
        try:
            id = int(str(to_).replace("<@!", "").replace(">", ""))
            to_ = getAddr(id)[0]
        except:
            continue_ = False
            MemberError = True
            embed.add_field(name='Error ❌', value='Wallet not found, please use @UserName or ``0xSiriWallet`` on the ``to`` parameter)')
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()
            continue_ = False

    if continue_:
        WalletName = str(ctx.author.id)
    
        doc_ref = db.collection(Collection).document(str(ctx.author.id))
        doc = doc_ref.get()

        keys_doc_ref = db.collection(Keys_Collection).document(WalletName)
        keys_doc = keys_doc_ref.get()

    if doc.exists and continue_: 
        totp = pyotp.TOTP(doc.to_dict()['base32Secret'])

        if int(totp.now())==int(otp_input):
            continue_ = True
        else:

            if doc.exists and otp_input!=0:
                embed.add_field(name='Error!', value="Wrong OTP!")
                embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
                await ctx.reply(embed=embed)
                embed.clear_fields()
                embed.remove_author()

            if doc.exists and otp_input==0:
                embed.add_field(name='Error!', value="Please specify the OTP!")
                embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
                await ctx.reply(embed=embed)
                embed.clear_fields()
                embed.remove_author()

    if not keys_doc.exists and continue_ and not MemberError:
        continue_ = False
        if CreateWallet(int(WalletName)) == True:
            embed.add_field(name="Error ❌", value="My bad, please run the command again")
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()

    if continue_:
        if not siri.is_address(to_):
            embed.add_field(name='Error ❌', value="Invalid recipient!")
            embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
            await ctx.reply(embed=embed)
            embed.clear_fields()
            embed.remove_author()

        if siri.is_address(to_):
            if (amount == 0) or (float(amount) > float(siri.balance(str(keys_doc.to_dict()["address"])))) :
                embed.add_field(name='Error ❌', value="Insufficient funds, you have: " + str(siri.balance(keys_doc.to_dict()["address"])) + " " + Cointicker)
                embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
                await ctx.reply(embed=embed)
                embed.clear_fields()
                embed.remove_author()
            else:
                txID = siri.transaction(keys_doc.to_dict()["privKey"], keys_doc.to_dict()["address"], to_, amount)
                    
                embed.add_field(name='Success!', value='You sent '+str(amount) + " " +Cointicker + ' to: ``' + getUser(to_) + str("``, [explorer](" + explorer + str(txID) + str(")") + "\n **TX ID:** ``"  + str(txID) + "``" ))
                embed.set_author(name=str(ctx.author), icon_url=(ctx.author).avatar_url)
                await ctx.reply(embed=embed)
                embed.clear_fields()
                embed.remove_author()



    WalletName = ""
    embed.clear_fields()
    embed.remove_author()
            

                    

        
bot.run(DiscordToken) # inputs your auth token

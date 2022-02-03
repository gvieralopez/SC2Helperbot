
TEMPLATE_SETTINGS = """
<b>SC2 Helper Settings</b>

💬 <b>Telegram</b>
<i>User:</i> @{0.arroba} 
<i>id:</i> <code>{0.tgid}</code>

🎮 <b>StarCraft II</b>
<i>Name:</i> <code>{0.display_name}</code>
<i>Battle Tag:</i> <code>{0.battle_tag}</code> /battletag
<i>Region ID:</i> /regionid 
    🇺🇸 <code>{0.US_id}</code>
    🇪🇺 <code>{0.EU_id}</code>
    🇰🇷 <code>{0.KR_id}</code>
    🇹🇼 <code>{0.TW_id}</code> 

<b>Last Updated:</b> {1} 
"""

TEMPLATE_MORE_DATA = """
Dear @{0.arroba}:

You have not entered sufficient information for me to track your progress in Battle Net.

<b>Please provide one of the following:</b>

<code>Region ID:</code> /regionid 
<code>Battle Tag:</code>  /battletag 

ℹ️ If you want to know the information I store from you,
You can check /settings
"""

TEMPLATE_BLIZZARD_ID = """
In order to get Blizzard Region ID, you need to send me your <i>Blizzard Profile URL:</i>

<code>/regionid [your_blizzard_URL]</code>

<b>To get your Blizzard Id:</b>

1️ Go to https://starcraft2.com/ and log in.
2️ Clic in view profile
3️ Copy the URL of your profile
4️ Send it to me using /regionid command

<b>Example</b>:

<code>/regionid https://starcraft2.com/en-us/profile/1/1/10993388</code>
"""

TEMPLATE_BATTLE_TAG = """
A Battle tag is a combination of Display name and a code that identifies a user in Blizzard games. I looks like:

<code>MyName#12345</code>

You can check your Battle tag in the Battle Net app, near the top right corner.

To send me your Battle tag you can use something:

<code>/battletag [battletag]</code>

<b>Example</b>:

<code>/battletag MyName#12345</code>
"""
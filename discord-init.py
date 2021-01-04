import discord, logging, re, os, json
from discord.ext import commands
import mistranslate as mt

#Initial setup
logging.basicConfig(level=logging.INFO)

__location__ = os.path.join(os.getcwd(),os.path.dirname(__file__))
conf_filepath = os.path.join(__location__, 'config.json')
__cache__ = os.path.join(__location__, 'filecache')
config = None

try:
    cfgfile = open(conf_filepath)
    cfgjson = cfgfile.read()
    config = json.loads(cfgjson)
except FileNotFoundError:
    print("FATAL: 'config.json' file not found. Unable to log into Discord account. Exiting.")
    exit(1)

if not os.path.isdir(__cache__):
    os.mkdir(__cache__)
    
#Checking config for missing values
if 'errormsg-time' not in config:
    print("WARNING: Value 'errormsg-time' not found in config. Falling back to default error message lifetime of 120 seconds.")
    config['errormsg-time'] = 120

#custom functions
async def send_parse_error(ctx,message):
    cmd = ctx.message.content
    if len(cmd) > 1024:
        cmd = cmd[:1021]+'...'
    embed = discord.Embed(title='Parse Error',description="I can't make sense of this command. Did you mistype?",colour=0xff0000)
    embed.add_field(name='Command',value=cmd)
    embed.add_field(name='Error',value=message)
    await ctx.send(ctx.author.mention,embed=embed,delete_after=config['errormsg-time'])
    
async def send_value_error(ctx,message):
    cmd = ctx.message.content
    if len(cmd) > 1024:
        cmd = cmd[:1021]+'...'
    embed = discord.Embed(title='Value Error',description="One or more values you put in aren't quite right.",colour=0xff0000)
    embed.add_field(name='Command',value=cmd)
    embed.add_field(name='Error',value=message)
    await ctx.send(ctx.author.mention,embed=embed,delete_after=config['errormsg-time'])
    
async def send_tl_error(ctx,inputstr,message):
    if len(inputstr) > 1024:
        inputstr = inputstr[:1021]+'...'
    embed = discord.Embed(title='Translation Error',description="Something went wrong while translating this text.",colour=0xff0000)
    embed.add_field(name='Input',value=inputstr)
    embed.add_field(name='Error',value=message)
    await ctx.send(ctx.author.mention,embed=embed,delete_after=config['errormsg-time'])

async def send_result(ctx,resultinfo,verbose=False,dump=False):
    #Check to make sure the input and output fit in the embed
    rfile=None
    if len(resultinfo['input']) > 1024 or len(resultinfo['iters'][-1]['result']) > 1024 or dump:
        #TODO: If it's too big to fit on an embed, send it as an external file instead
        await send_tl_error(ctx,resultinfo['input'],"Input and output values that are 1024 characters in length aren't supported yet.")
        return
        #rfname = 
    else:
        embed = discord.Embed(title='Translation Result',colour=0x00ff3f)
        embed.add_field(name='Input',value=resultinfo['input']) 
        if verbose:
            embed.add_field(name='Input Language',value=resultinfo['inputlangname']+' ('+resultinfo['inputlang']+')')
            embed.add_field(name='Iterations',value=str(len(resultinfo['iters'])))
            embed.add_field(name='Output Language',value=resultinfo['iters'][-1]['langname'])
        embed.add_field(name='Output',value=resultinfo['iters'][-1]['result'])
    await ctx.send(ctx.author.mention,embed=embed,file=rfile)
    
#Command parser
cmdbot = commands.Bot(command_prefix='mistl:')

@cmdbot.command(aliases=['tl','t'])
async def translate(ctx, *args):
    args = list(args)
    
    #set up variables
    inputstr = None
    
    flags = {}
    mode = 0
    langlist = None
    
    #Check arguments
    while args:
        curarg = args.pop(0)
        #Check flag
        if curarg.startswith('-'):
            #Disallow composite arguments
            if len(curarg) > 2:
                await send_parse_error(ctx,'Composite flags (i.e. flags with multiple option tags in one, like -vd) are not allowed.')
                return
            #Warn about stray dashes/blank options
            elif len(curarg) == 1:
                await send_parse_error(ctx,'Blank flags (i.e. lone dashes that are not part of the translation input) are not allowed as arguments.')
                return
            #Check for duplicate flag
            elif curarg in flags:
                await send_parse_error(ctx,f'Duplicate flag detected: `{curarg}`')
                return
            else:
                #Process the option flag
                #Check if flag requires input
                if curarg[1] in ('i','o','t','l','L','s'):
                    #Throw error if there's no more input
                    if not args:
                        await send_parse_error(ctx,f'Flag `{curarg}` requires input, but no further input was detected.')
                        return
                    else:
                        flags[curarg] = args.pop(0)
                else:
                    flags[curarg] = True
        else:
            #If there are no more flags, treat the rest of the input as the text to translate
            inputstr = curarg + ' ' + ' '.join(args)
            break
    #TODO: Check for mutually exclusive flags, set listmode and langlist
    if '-s' in flags:
        if ('-o' in flags or '-t' in flags or '-l' in flags or '-L' in flags):
            await send_parse_error(ctx,'The `-s` flag may not be used in conjunction with `-o`,`-t`,`-l`, or `-L`.')
            return
        langlist = flags['-s']
        mode = 3
    if '-l' in flags and '-L' in flags:
        await send_parse_error(ctx,'`-l` and `-L` cannot be used together.')
        return
    if '-l' in flags:
        langlist = flags['-l']
        mode = 2
    if '-L' in flags:
        langlist = flags['-L']
        mode = 1
    if '-t' in flags:
        try:
            flags['-t'] = int(flags['-t'])
        except:
            send_parse_error(ctx,'`-t` requires an integer value.')
    
    print(f"\nSENDER: {ctx.message.author.name}\nINPUT: {inputstr}\nTYPE: {type(inputstr)}\nMODE: {mode}\nLIST: {langlist}")
    
    #Start translation
    tlcl = mt.mt_Client()
    result = None
    await ctx.trigger_typing()
    try:
        result = tlcl.chain_translate(inputstr,mode,flags.get('-o',None),flags.get('-t',0),flags.get('-i',None),langlist)
    except (TypeError,ValueError) as e:
        await send_value_error(ctx,str(e))
        return
    except Exception as e:
        await send_tl_error(ctx,inputstr,str(e))
        return
    await send_result(ctx,result,'-v' in flags,'-d' in flags)
    print("TL_DONE")
    return
#TODO: Help function, standalone language detection, about

@translate.error
async def translate_error(ctx, error):
    if isinstance(error,commands.errors.UnexpectedQuoteError):
        await send_parse_error(ctx, "Unexpected quote mark in input. Make sure to properly escape your double quotes (using '\\\\\"').")
    else:
        print(','.join(error.args))
        

@cmdbot.event
async def on_ready():
    print('Login successful. Username: {0}'.format(cmdbot.user.name))

cmdbot.run(config['discord-auth-token'])

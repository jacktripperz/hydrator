import json
import time
import contract as c
from price import get_drip_price
from datetime import datetime
import time

drip_contract_addr = "0xFFE811714ab35360b67eE195acE7C10D93f89D8C"
wallet_public_addr = "0x361472B5784e83fBF779b015f75ea0722741f304"
loop_sleep_seconds = 60
start_polling_threshold_in_seconds = 60*10

# load private key
wallet_private_key = open('key.txt', "r").readline()

# load abi
f = open('faucet_abi.json')
faucet_abi = json.load(f)

# create contract
faucet_contract = c.connect_to_contract(drip_contract_addr, faucet_abi)

# cycle class
class cycleItem: 
    def __init__(self, id, type, minimumDrip): 
        self.id = id 
        self.type = type
        self.minimumDrip = minimumDrip

# cycle types are "hydrate" or "claim"
cycle = [] 
cycle.append( cycleItem(1, "hydrate", 0.04) )
cycle.append( cycleItem(2, "hydrate", 0.04) )
cycle.append( cycleItem(3, "hydrate", 0.04) )
cycle.append( cycleItem(4, "hydrate", 0.04) )
cycle.append( cycleItem(5, "hydrate", 0.04) )
cycle.append( cycleItem(6, "hydrate", 0.04) )
cycle.append( cycleItem(7, "hydrate", 0.04) )
nextCycleId = 1

def deposit_amount(addr):
    user_totals = faucet_contract.functions.userInfoTotals(addr).call()
    return user_totals[1]/1000000000000000000

def available(addr):
    return faucet_contract.functions.claimsAvailable(addr).call() / 1000000000000000000

def hydrate():
    txn = faucet_contract.functions.roll().buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def claim():
    txn = faucet_contract.functions.claim().buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def buildTimer(t):
    mins, secs = divmod(int(t), 60)
    hours, mins = divmod(int(mins), 60)
    days, hours = divmod(int(hours), 24)
    timer = '{:02d} days, {:02d} hours, {:02d} mins, {:02d} seconds'.format(days, hours, mins, secs)
    return timer

def countdown(t):
    while t:
        print(f"Next poll in: {buildTimer(t)}", end="\r")
        time.sleep(1)
        t -= 1

def findCycleMinimumDrip(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.minimumDrip
            break
        else:
            x = None

def findCycleType(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.type
            break
        else:
            x = None

def getNextCycleId(currentCycleId):
    cycleLength = len(cycle)
    if currentCycleId == cycleLength:
        return 1
    else:
        return currentCycleId + 1

    
# create infinate loop that checks contract every set sleep time
nextCycleType = findCycleType(nextCycleId)
while True:
    deposit = deposit_amount(wallet_public_addr)
    avail = available(wallet_public_addr)
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%b-%Y (%H:%M:%S)]")

    cycleMinimumDrip = findCycleMinimumDrip(nextCycleId)

    dripPerDay = deposit * 0.01
    dripPerSecond = dripPerDay / 24 / 60 / 60
    secondsUntilHydration = (cycleMinimumDrip - avail) / dripPerSecond
    
    sleep = loop_sleep_seconds

    if secondsUntilHydration > start_polling_threshold_in_seconds:
        sleep = secondsUntilHydration - start_polling_threshold_in_seconds
    
    if avail > cycleMinimumDrip:
        if nextCycleType == "hydrate":
            hydrate()
        if nextCycleType == "claim":
            claim()
        
        new_deposit = deposit_amount(wallet_public_addr)
        drip_price = get_drip_price()
        total_value = new_deposit * drip_price

        if nextCycleType == "hydrate":
            print("********** HYDRATED *******")
            print(f"{timestampStr} Added to deposit: {avail:.3f}")
        if nextCycleType == "claim":
            print("********** CLAIMED ********")
            print(f"{timestampStr} Claimed {avail:.3f} drip!")
        
        print(f"{timestampStr} New total deposit: {new_deposit:,.2f}")
        print(f"{timestampStr} New total value: {total_value:,.2f}")

        nextCycleId = getNextCycleId(nextCycleId)
        nextCycleType = findCycleType(nextCycleId)
        print(f"{timestampStr} Next cycle type will be: {nextCycleType}")
        print("***************************")
    else:
        print("********** STATS *******")
        print(f"{timestampStr} Deposit: {deposit:.3f}")
        print(f"{timestampStr} Minimum hydrate amount: {cycleMinimumDrip:.3f}")
        print(f"{timestampStr} Available to hydrate: {avail:.3f}")
        print(f"{timestampStr} Drip per second: {dripPerSecond:.8f}")
        print(f"{timestampStr} Until next hydration: {buildTimer(secondsUntilHydration)}")
        print(f"{timestampStr} Start polling each {(loop_sleep_seconds / 60)} minute {(start_polling_threshold_in_seconds / 60):.0f} minutes before next hydration")
        print("************************")

    countdown(int(sleep))
    

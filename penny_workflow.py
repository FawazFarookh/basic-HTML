import os
import getpass
import copy
import collections
from io import BytesIO
import json
from datetime import datetime, timedelta, date
from dateutil import parser

import requests
import pandas as pd


def iso_default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()[:-3] + "Z"


def delete_keys_except(dictionary, keep_keys):
    keys_to_delete = []
    for key in dictionary:
        if key not in keep_keys:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del dictionary[key]


email = "fawaz.farookh@penny.co"
password = "Fawaz11$$"
base_url = "https://api-test.penny.co/api"

r = requests.post(
    base_url + "/auth/login",
    json={"email": email, "password": password, "remember": ""},
)
if r.status_code == 201:
    access_token = r.json()["accessToken"]
headers = {"Authorization": f"Bearer {access_token}"}
r.status_code

headers = {"Authorization": f"Bearer {access_token}"}

first_name = ""
last_name = ""
currency = "SAR"
user_id = ""
req_user = {
    "type": "USER",
    "performer": {
        "id": user_id,
        "email": email,
        "name": first_name,
        "type": "ORG-USER",
    },
}

# getting products
r = requests.get(
    base_url + "/products",
    headers=headers,
)
req_products = r.json()["products"][:2]

# getting the vendors
r = requests.get(
    base_url + "/vendors?",
    headers=headers,
)
rfq_vendors = r.json()["vendors"][:2]

# getting the workspace keys

workspace_keys = ["id", "name", "startDate", "endDate", "currency", "locations"]

r = requests.get(
    base_url + "/workspaces",
    headers=headers,
)
wkp = r.json()["workspaces"][0]
delete_keys_except(wkp, workspace_keys)
wkp

# creating and calling the request

request_payload = {
    "id": "",
    "title": "Sample Request - Refreshment",
    "requestedDate": datetime.utcnow().isoformat()[:-3] + "Z",
    "expectedDate": (datetime.utcnow() + timedelta(days=10)).isoformat()[:-3] + "Z",
    "requestor": req_user,
    "workspace": wkp,
    "items": [],
    "location": wkp["locations"][0],
    "requestType": "PRODUCT_REQUEST",
    "status": "REQUEST_DRAFTED",
    "cuurency": "",
    "requestPriority": "LOW",
    "comments": {},
    "attachments": [],
    "inventory": None,
}

r = requests.post(
    base_url + "/request",
    headers=headers,
    json=json.loads(json.dumps(request_payload, default=iso_default)),
)

req_id = r.json()["id"]
req_id
request_payload.update(r.json())

items = []
for prod in req_products:
    item = dict()
    item["allowDifferentBrand"] = False
    item["allowAlternateProduct"] = False
    item["status"] = True
    item["name"] = prod["name"]
    item["product"] = prod
    item["quantity"] = 1
    item["price"] = prod["price"]
    item["vendor"] = []
    item["type"] = "PRODUCT_REQUEST"
    items.append(item)
items

request_payload["items"] = items

r = requests.put(
    base_url + "/request",
    headers=headers,
    json=json.loads(json.dumps(request_payload, default=iso_default)),
)
r.status_code

request_payload.update(r.json())

r = requests.get(
    base_url + f"/rfqs/request/{req_id}",
    headers=headers,
)
print(r.status_code)
rfq_payload = r.json()
request_payload["bidType"] = "OPEN_BID"

r = requests.post(
    base_url + f"/request/submit",
    headers=headers,
    json=json.loads(json.dumps(request_payload, default=iso_default)),
)
print(r.status_code)

vendors_items = [
    {"contractId": None, "price": None, "connectionId": v["id"]} for v in rfq_vendors
]

rfq_vendor_config = dict()
for vendor in rfq_vendors:
    rfq_vendor_config[vendor["id"]] = {
        "config": {
            "shippingTerms": [
                {"value": "EXW", "label": " Ex Works (EXW)"},
                {"value": "FCA", "label": "Free Carrier (FCA)"},
                {"value": "CPT", "label": "Carriage Paid To (CPT)"},
                {"value": "CIP", "label": "Carriage and Insurance Paid to (CIP)"},
                {"value": "DPU", "label": "Delivered At Place Unloaded (DPU)"},
                {"value": "DAP", "label": "Delivered At Place (DAP)"},
                {"value": "DDP", "label": "Delivered Duty Paid (DDP)"},
                {"value": "FAS", "label": "Free Alongside Ship (FAS)"},
                {"value": "FOB", "label": "Free on Board (FOB)"},
                {"value": "CFR", "label": "Cost and Freight (CFR)"},
                {"value": "CIF", "label": "Cost, Insurance & Freight (CIF)"},
            ],
            "paymentTerms": [],
            "paymentOptions": ["BEFORE_DELIVERY", "AFTER_DELIVERY"],
        },
        "recipients": vendor["vendorAdditionalInfo"]["details"]["contacts"],
    }

    request_items = request_payload["items"]
for item in request_items:
    item["vendors"] = vendors_items
rfq_options = {
    "expDate": request_payload["expectedDate"],
    "deliveryDate": request_payload["expectedDate"],
    "contactInfo": {
        "name": f"{first_name} {last_name}",
        "email": email,
    },
    "comments": "<p>Need these items as soon as possible</p>",
    "attachments": [],
    "RFQVendorConfig": rfq_vendor_config,
    "requestTypes": {req_id: ["PRODUCT_REQUEST"]},
    "bidType": "OPEN_BID",
    "paymentPlan": [],
}

rfq_payload = {
    "requestItems": request_payload["items"],
    "rfqOptions": rfq_options,
}

r = requests.put(
    base_url + f"/rfqs/generate-rfqs/{req_id}",
    headers=headers,
    json=json.loads(json.dumps(rfq_payload, default=iso_default)),
)
r.status_code

r = requests.get(
    base_url + f"/rfqs/request/{req_id}",
    headers=headers,
)
rfqs = r.json()

for rfq in rfqs:
    rfq_id = rfq["id"]
    r = requests.post(
        base_url + "/rfqs/offer/compare/", headers=headers, json={"rfqIds": [rfq_id]}
    )
    print(r.status_code)


token = rfqs[0]["token"]
files = {
    "file": (
        "test.pdf",
        open("D:\\penny test101\\test.pdf", "rb"),
        "application/pdf",
    )
}
r = requests.post(base_url + f"/rfq_vendor/ANY/rfq-vendor/{token}", files=files)
r.status_code

file_path = r.json()["uploadStatus"]["path"]

tax = 1.15
tax_item = {"id": 1, "name": "VAT", "description": "", "taxType": "%", "value": 15}
ship_prices_list = [3.0, 5.0]
prod_prices_list = [(40.0, 13.0), (45.0, 14.5)]
total_list = []
for i in range(len(prod_prices_list)):
    total_list.append(
        round(
            sum([x * tax for x in prod_prices_list[i]]) + ship_prices_list[i] * tax, 2
        )
    )


vendor_offers = []
index = 0
attachments = [file_path]
for rfq in rfqs:
    token = rfq["token"]
    r = requests.get(
        base_url + f"/rfq_vendor/{token}",
        headers=headers,
    )
    offer_payload = r.json()
    attachments = [file_path]
    if index > 0:
        attachments = []

    offer_payload.update(
        {
            "attachments": attachments,
            "shippingFee": round(ship_prices_list[index] * tax, 2),
            "shippingFeeSubTotal": ship_prices_list[index],
            "shippingFeeTax": [tax_item],
            "subTotal": round(sum(prod_prices_list[index]), 2),
            "total": total_list[index],
            "paymentTermType": "AFTER_DELIVERY",
            "shipmentTerm": "FCA",
            "offerExpiryDate": (datetime.utcnow() + timedelta(days=30)).isoformat()[:-3]
            + "Z",
            "comments": {
                "rfqBuyerComments": '<p><span style="background-color: rgb(255, 255, 255);">Need these items as soon as possible</span></p>',
                "actionComments": [],
                "vendorRemarks": '<p><span style="background-color: rgb(255, 255, 255);">Pleased to submit our offer to you. For any queries, please contact us at any time</span></p>',
            },
        }
    )

    for i in range(len(offer_payload["rfqItems"])):
        offer_payload["rfqItems"][i]["offer"]["offerTotal"] = round(
            prod_prices_list[index][i] * tax, 2
        )
        offer_payload["rfqItems"][i]["offer"]["eta"] = 10
        price = {
            "basePrice": prod_prices_list[index][i],
            "value": round(prod_prices_list[index][i] * tax, 2),
            "currency": currency,
            "taxes": [tax_item],
        }
        offer_payload["rfqItems"][i]["offer"]["price"] = price
        offer_payload["rfqItems"][i]["isAvailable"] = True
        offer_payload["rfqItems"][i]["markupValue"] = 0

    r = requests.put(
        base_url + f"/rfq_vendor/{token}",
        headers=headers,
        json=json.loads(json.dumps(offer_payload, default=iso_default)),
    )
    index += 1
    print(rfq["id"], r.status_code)
    vendor_offers.append({"rfq_id": rfq["id"], "response": r.json()})


disqualified_id = vendor_offers[-1]["rfq_id"]
r = requests.post(
    base_url + f"/rfqs/offer-action/{disqualified_id}",
    headers=headers,
    json={"offerActionType": "DISQUALIFY"},
)
r.status_code

r = requests.get(
    base_url + f"/rfqs/request/{req_id}",
    headers=headers,
)
revised_id = vendor_offers[1]["rfq_id"]
for x in r.json():
    if x["id"] == revised_id:
        revise_offer = x
revise_payload = copy.deepcopy(revise_offer)
revise_payload["rfqItems"][0]["requestorPrice"] = 43
revise_payload["negotiateValues"] = {}
revise_payload["previousOffers"] = [
    {
        "offerReceivedDate": revise_offer["offerReceivedDate"],
        "revisionSubmittedDate": datetime.utcnow().isoformat()[:-3] + "Z",
        "reason": "",
        "attachments": [],
        "rfqItems": revise_offer["rfqItems"],
        "comments": revise_offer["comments"],
        "shipmentTerm": revise_offer["shipmentTerm"],
        "shippingFee": revise_offer["shippingFee"],
        "shippingFeeSubTotal": revise_offer["shippingFeeSubTotal"],
        "shippingFeeTax": revise_offer["shippingFeeTax"],
        "paymentTerm": revise_offer["paymentTerm"],
        "subTotal": revise_offer["subTotal"],
        "total": revise_offer["total"],
        "offerRevisedBy": "BUYER",
        "negotiateValues": revise_offer["negotiateValues"],
        "status": revise_offer["status"],
        "buyerAttachments": revise_offer["buyerAttachments"],
        "paymentPlan": revise_offer["paymentPlan"],
    }
]
revise_payload["comments"]["buyerNegotiationRemarks"] = ""
r = requests.put(
    base_url + "/rfqs/revise",
    headers=headers,
    json=json.loads(json.dumps(revise_payload, default=iso_default)),
)

r.status_code

r = requests.get(
    base_url + f"/rfqs/request/{req_id}",
    headers=headers,
)
offer_id = vendor_offers[0]["rfq_id"]
for x in r.json():
    if x["id"] == offer_id:
        accepted_offer = x
accepted_offer["comments"][
    "buyerAcceptRemarks"
] = "<p>Offer looks good. Approved</p><p><br></p>"

r = requests.put(
    base_url + "/rfqs/offer",
    headers=headers,
    json=json.loads(json.dumps(accepted_offer, default=iso_default)),
)
r.status_code


r = requests.post(base_url + f"/orders/create/{offer_id}", headers=headers, json={})
r.status_code

order_resp = r.json()
order_id = order_resp["id"]
order_id

order_payload = {
    "terms": order_resp["terms"],
    "attachments": order_resp["attachments"],
    "itemExpenseAccount": [
        {"productId": x["product"]["id"]} for x in order_resp["items"]
    ],
}
order_payload
r = requests.put(
    base_url + f"/orders/submit/{order_id}",
    headers=headers,
    json=order_payload,
    params={"generateGDN": "false"},
)
r.status_code

grn_payload = {
    "grn": [
        {"productId": x["product"]["id"], "quantity": 1} for x in order_resp["items"]
    ],
    "attachments": order_resp["attachments"],
    "remarks": {"grnRemarks": "", "gdnRemarks": "", "setupInstructions": ""},
    "earlyClose": False,
}
r = requests.post(
    base_url + f"/grns/{order_id}",
    headers=headers,
    json=grn_payload,
)
r.status_code

files = {
    "file": (
        "invoice_dummy.pdf",
        open("D:\invoice\invoice_dummy.pdf", "rb"),
        "application/pdf",
    )
}
r = requests.post(
    base_url + "/media_upload/ANY/bills",
    headers=headers,
    files=files,
)
r.status_code


invoice_path = r.json()["uploadStatus"]["path"]

r = requests.post(
    base_url + f"/bills/create/{order_id}",
    headers=headers,
    json={},
)
r.status_code

bill_resp = r.json()

bill_resp["billDue"] = (datetime.utcnow() + timedelta(days=30)).isoformat()[:-3] + "Z"
bill_resp["attachments"] = [invoice_path]
bill_resp["status"] = "BILL_SUBMITTED"

r = requests.put(base_url + "/bills/submit", headers=headers, json=bill_resp)
r.status_code

bill_payload = r.json()
bill_id = bill_payload["id"]

r = requests.get(
    base_url + f"/bills/submitted/{bill_id}", 
    headers=headers
)
for bill in r.json():
    if bill["id"] == bill_id:
        bill_resp = bill
        
account = {"id":"1","accountName":"Active Running Account",
           "accountNumber":"1234","_id":"6408662114e16948fead6281","bankName":"Nationa"}

payment_payload = {
    "account": account,
    "attachments": [], 
    "bills": [bill_resp], 
    "paymentBillAmount": {
        bill_id: bill_resp["billTotal"]
    }, 
    "proformaCredit": 0, 
    "vendor": bill_resp["vendor"], 
    "vendorCredit": 0,
}

r = requests.post(
    base_url + "/payments/submit", 
    headers=headers, 
    json=payment_payload,
)
r.status_code

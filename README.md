# Nutrient Collaborative Test

https://nutrient-collab-test.fly.dev/

This is a test application demonstrating a collaborative signing flow using Nutrient's Document Engine.

# Bug 1

### Instructions (https://support.nutrient.io/hc/requests/129650)

1. open https://nutrient-collab-test.fly.dev/
2. click "Generate Document"
3. click "Generate Buyer Link" and open the generated link.
4. click the seller signature field and press Enter key on keyboard.
5. This will open the signature popup and let the buyer sign on the seller signature box. 

### Bug Demo

https://github.com/user-attachments/assets/2227a96e-5dd4-4cb4-9842-be27178a8511

# Bug 2

### Instructions 

1. open https://nutrient-collab-test.fly.dev/
2. click "Generate Document"
3. click "Generate Buyer Link" and open the generated link.
4. open inspect element and paste this snippet

    const container=document.getElementById("doc-container");const unloaded=PSPDFKit.unload(container);PSPDFKit.load({container:"#doc-container",documentId:documentId,authPayload:{jwt:jwtToken},serverUrl:engineUrl,instant:true}).then((instance)=>{const circle=new PSPDFKit.Annotations.EllipseAnnotation({pageIndex:0,boundingBox:new PSPDFKit.Geometry.Rect({left:100,top:100,width:100,height:100})});instance.create(circle)}).catch((error)=>{});

6. You should see a permanent circle (it persists page refresh)


## Run this locally

Install [uv](https://github.com/astral-sh/uv) 

    uv run ./app.py

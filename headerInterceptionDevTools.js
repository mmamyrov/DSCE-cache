const puppeteer = require("puppeteer");
test();
async function test() {
  const browser = await puppeteer.launch({
    //   headless: false,

  });
  const page = await browser.newPage();
  const client = await page.target().createCDPSession();

  await client.send("Fetch.enable", {
    patterns: [{
        urlPattern: '*', 
        requestStage: "Response" }]
  });

    client.on("Fetch.requestPaused", async (reqEvent) => {
    const { requestId } = reqEvent;
    console.log(`Request "${requestId}" paused.`);

    let responseHeaders = reqEvent.responseHeaders || [];
    // console.log(reqEvent.responseHeaders);
    for (let elements of responseHeaders) {
        if (elements.name.toLowerCase() === 'cache-control') {
            if (elements.value.includes("max-age")){
                const CP = elements.value.split("max-age");
                resp=""
                for (let x = 0; x < CP.length-1; x++) {
                    resp+=CP[x]
                }
                elements.value=resp+"max-age=0"
            }
        }
    }
    // const responseObj = await client.send('Fetch.getResponseBody', {
    //     requestId,
    // });
    // await client.send('Fetch.fulfillRequest', {
    //     requestId,
    //     responseCode: 200,
    //     responseHeaders,
    //     body: responseObj.body,
    // });
    

    // } else {
    //   // If the content-type is not what we're looking for, continue the request without modifying the response
    //   await client.send('Fetch.continueRequest', { requestId });
    // }
    await client.send("Fetch.continueResponse", { requestId, responseCode: 200, responseHeaders });
    console.log(reqEvent.responseHeaders);
  });

  await page.goto("http://www.google.com");
//   await page.waitFor(100000);
  await browser.close();
  return;
}
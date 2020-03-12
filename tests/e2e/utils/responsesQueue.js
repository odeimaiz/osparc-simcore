const utils = require("./utils")

class ResponsesQueue {
  constructor(page) {
    this.__page = page;
    this.__reqQueue = [];
    this.__respPendingQueue = [];
    this.__respReceivedQueue = {};
  }

  addResponseListener(url) {
    const page = this.__page;
    const reqQueue = this.__reqQueue;
    const respPendingQueue = this.__respPendingQueue;
    const respReceivedQueue = this.__respReceivedQueue;
    reqQueue.push(url);
    respPendingQueue.push(url);
    respReceivedQueue[url] = null;
    console.log("-- Expected response added to queue", url);
    page.on("request", function callback(req) {
      if (req.url().includes(url)) {
        console.log((new Date).toUTCString(), "-- Queued request sent", req.url());
        page.removeListener("request", callback);
        const index = reqQueue.indexOf(url);
        if (index > -1) {
          reqQueue.splice(index, 1);
        }
      }
    });
    page.on("response", function callback(resp) {
      if (resp.url().includes(url)) {
        console.log((new Date).toUTCString(), "-- Queued response received", resp.url(), ":");
        resp.json().then(data => {
          console.log("url response", typeof data);
          respReceivedQueue[url] = data;
        });
        page.removeListener("response", callback);
        const index = respPendingQueue.indexOf(url);
        if (index > -1) {
          respPendingQueue.splice(index, 1);
        }
      }
    });
  }

  isRequestInQueue(url) {
    return this.__reqQueue.includes(url);
  }

  isResponseInQueue(url) {
    return this.__respPendingQueue.includes(url);
  }

  async waitUntilResponse(url, timeout = 10000) {
    let sleptFor = 0;
    const sleepFor = 100;
    while (this.isResponseInQueue(url) && sleptFor < timeout) {
      await utils.sleep(sleepFor);
      sleptFor += sleepFor;
    }
    console.log("-- Slept for", sleptFor/1000, "s waiting for", url);
    if (sleptFor >= timeout) {
      throw("-- Timeout reached." + new Date().toUTCString());
    }
    else {
      const resp = this.__respReceivedQueue[url];
      if ("error" in resp && resp["error"] !== null) {
        throw("-- Error in response", resp["error"]);
      }
      return resp["data"];
    }
  }
}

module.exports = {
  ResponsesQueue
}

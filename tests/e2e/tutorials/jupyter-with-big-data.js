// node jupyter-with-big-data.js [url] [user] [password] [--demo]

const utils = require('../utils/utils');
const tutorialBase = require('./tutorialBase');

const args = process.argv.slice(2);
const {
  url,
  user,
  pass,
  newUser,
  startTimeout,
  enableDemoMode
} = utils.parseCommandLineArguments(args)

const serviceName = "JupyterLab sim4life";

async function runTutorial() {
  const tutorial = new tutorialBase.TutorialBase(url, serviceName, user, pass, newUser, enableDemoMode);
  let studyId
  try {
    await tutorial.start();
    const studyData = await tutorial.openService(1000);
    studyId = studyData["data"]["uuid"];

    const workbenchData = utils.extractWorkbenchData(studyData["data"]);
    console.log(workbenchData);
    await tutorial.waitForServices(
      workbenchData["studyId"],
      [workbenchData["nodeIds"][0]],
      startTimeout,
      false
    );

    // open JLab
    await tutorial.waitFor(10000, "wait for jupyter lab to appear...")
    await tutorial.takeScreenshot("opened " + serviceName);

    // get the file menu
    const iframeHandles = await tutorial.getIframe();
    let iframes2 = [];
    for (let i = 0; i < iframeHandles.length; i++) {
      const frame = await iframeHandles[i].contentFrame();
      iframes2.push(frame);
    }
    const jLabIframe = iframes2.find(iframe => iframe._url.includes(workbenchData["nodeIds"][0]));
    await utils.waitAndClick(jLabIframe, '#jp-MainMenu > ul > li:nth-child(1)', 35000);
    await tutorial.takeScreenshot("opened_File_menu");
    // click the New entry
    await utils.waitAndClick(jLabIframe, "#jp-mainmenu-file > ul > li:nth-child(1) > div.lm-Menu-itemLabel.p-Menu-itemLabel");
    await tutorial.takeScreenshot("opened_File_New_entry");
    // click the Terminal entry
    await utils.waitAndClick(jLabIframe, "#jp-mainmenu-file-new > ul > li:nth-child(3) > div.lm-Menu-itemLabel.p-Menu-itemLabel")
    await tutorial.takeScreenshot("created_File_New_Terminal_entry");
    await tutorial.waitFor(3000, "wait for terminal to start...");
    await tutorial.takeScreenshot("terminal is up");
    await tutorial.__page.keyboard.type("cd work/workspace", {
      delay: 100
    });
    await tutorial.__page.keyboard.press("Enter", {
      delay: 100
    });
    await tutorial.takeScreenshot("terminal in workspace");
    await tutorial.__page.keyboard.type("fallocate -l 10G big_file.txt", {
      delay: 100
    });
    await tutorial.__page.keyboard.press("Enter", {
      delay: 100
    });
    await tutorial.takeScreenshot("terminal created big_file");
    await tutorial.__page.keyboard.type("ls -tlah", {
      delay: 100
    });
    await tutorial.__page.keyboard.press("Enter", {
      delay: 100
    });
    await tutorial.takeScreenshot("terminal ls");

    // back to dashboard
    await tutorial.toDashboard();

    // aprox 3' for 10GB
    await tutorial.waitFor(240000, "wait for study to close...");
  }
  catch (err) {
    tutorial.setTutorialFailed(true);
    console.log('Tutorial error: ' + err);
  }
  finally {
    await tutorial.toDashboard()
    await tutorial.removeStudy(studyId, 20000);
    await tutorial.logOut();
    await tutorial.close();
  }

  if (tutorial.getTutorialFailed()) {
    throw "Tutorial Failed";
  }
}

runTutorial()
  .catch(error => {
    console.log('Puppeteer error: ' + error);
    process.exit(1);
  });

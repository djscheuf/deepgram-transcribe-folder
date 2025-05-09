const path = require('path');
const fs = require("fs");

require('dotenv').config()
const { createClient } = require("@deepgram/sdk");

// Dependencies
const createDeepgramClient = () => createClient(process.env.DEEPGRAM_API_KEY);
const readFileSync = (fileName) => fs.readFileSync(fileName);
const writeFileSync = (filePath, data) => fs.writeFileSync(filePath, data);
const readdirSync = (dir) => fs.readdirSync(dir);

// Transcription
const transcribeContentWithTool = (readContentSync, transcriptionClient) => async (fileName) => {
  try {
  const content = readContentSync(fileName);
  const { result, error } = await transcriptionClient.listen.prerecorded.transcribeFile(
    content,
    {
      model: "nova-2",
      smart_format: true,
    }
  );
  if (error) throw error;
    // STEP 4: Print the results
    if (!error) {
      return result.results.channels[0].alternatives[0].transcript;
    }
  } catch (ex) {
    return ex.message;
  }
}
const transcribeFileWithDeepgram = transcribeContentWithTool(readFileSync, createDeepgramClient());

const outDir = "out";
const saveTo = (writeContentSync) = async (input) => {
    console.log(input)
    const {name,transcript} = input;
    const justName = path.parse(name).name;
    const outName = `${justName}.md`;
    const outPath = path.join(outDir,outName);
    const contents = await transcript;
    console.log(`Writing contents to: ${outPath}`)
    await writeContentSync(outPath,contents);
}
const saveToDisk = saveTo(writeFileSync);

const inDir = "./in/"
const files = readdirSync(inDir); // read fileNames in input folder.

const limiter = "2025"; // My Recorder names files by date of recording, starting with YYYYMM
const filteredFiles = files
  .filter(x=> x.startsWith(limiter)) // Limit Selections
  .map(x=>`${inDir}${x}`); // Properly provide Path

const toGroupBy7thChar = (agg, cur) => {
  agg[cur[6]].push(cur);
  return agg;
}

const batches = filteredFiles.reduce(toGroupBy7thChar,{"0":[], "1":[],"2":[],"3":[]});

// const batches = {"0":filteredFiles};

console.log(`All Batches: ${JSON.stringify(batches)}`);

Object.keys(batches).forEach(key => {
  console.log(` - - - - - Starting Batch: ${limiter} ${key} - - - - -`);
  const theBatch = batches[key];
  const batchTranscripts = theBatch.map(transcribeFile);
  Promise.all(batchTranscripts);

  const namesAndTranscripts = theBatch.map(function(name, i) {
    return {name, transcript:batchTranscripts[i]};
  });

  namesAndTranscripts.map(saveToDisk);

  console.log(` - - - - - Finished Batch: ${limiter} ${key} - - - - -`);
})

console.log(filteredFiles);
const transcripts = filteredFiles.map(transcribeFile);
Promise.all(transcripts);

const namesAndTranscripts = filteredFiles.map(function(name, i) {
    return {name, transcript:transcripts[i]};
  });

namesAndTranscripts.map(saveToDisk);

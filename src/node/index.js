import path from 'path';
import fs from 'fs';
import dotenv from 'dotenv';
import { createClient } from "@deepgram/sdk";
import { CLIENT_RENEG_WINDOW } from 'tls';

dotenv.config()

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
const saveTo = (writeContentSync) => async (input) => {
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

// Get limiter from command line arguments or use default
const DEFAULT_LIMITER = "2025080";
const limiter = process.argv[2] || DEFAULT_LIMITER;

// Show usage if help is requested
if (limiter === '--help' || limiter === '-h') {
  console.log('Usage: node index.js [limiter]');
  console.log('  limiter: Optional prefix to filter files (default: 2025080)');
  console.log('Example: node index.js 202407');
  process.exit(0);
}

console.log(`Using limiter: ${limiter}`);

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

// Object.keys(batches).forEach(key => {
//   console.log(` - - - - - Starting Batch: ${limiter} ${key} - - - - -`);
//   const theBatch = batches[key];
//   const batchTranscripts = theBatch.map(transcribeFileWithDeepgram);
//   Promise.all(batchTranscripts);

//   const namesAndTranscripts = theBatch.map(function(name, i) {
//     return {name, transcript:batchTranscripts[i]};
//   });

//   namesAndTranscripts.map(saveToDisk);

//   console.log(` - - - - - Finished Batch: ${limiter} ${key} - - - - -`);
// })

console.log(filteredFiles);
const transcripts = filteredFiles.map(transcribeFileWithDeepgram);
await Promise.all(transcripts);

const namesAndTranscripts = filteredFiles.map(function(name, i) {
    return {name, transcript:transcripts[i]};
  });

console.log(namesAndTranscripts);

namesAndTranscripts.map(saveToDisk);

import os from 'os';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import crypto from 'crypto';

async function checkPackageLock() {
    const targetDir = path.resolve(fs.mkdtempSync(path.join(os.tmpdir(), "beaker-package-lock-")));
    try {
        console.log(`Created temporary folder ${targetDir} for build.`);
        const origPackageLock = path.resolve('package-lock.json');
        const newPackageLock = path.join(targetDir, "package-lock.json");

        fs.copyFileSync("package.json", path.join(targetDir, "package.json"));
        fs.copyFileSync("lock.npmrc", path.join(targetDir, ".npmrc"));
        fs.cpSync("vendor", path.join(targetDir, "vendor"), {recursive: true});

        const cmd = `npm install --prefix=${targetDir} --package-lock-only`;
        const lockFileProcPromise = new Promise((resolve, reject) => {
            console.log(`Running '${cmd}`);
            const proc = exec(cmd);
            proc.stdout?.on('data', (data) => {
                console.log(data);
            });
            proc.stderr?.on('data', (data) => {
                console.log(data);
            });

            proc.on("exit", (code) => {
                if (code === 0) {
                    resolve(proc);
                }
                else {
                    reject(proc);
                }
            });
        });
        await lockFileProcPromise;

        if (fs.existsSync(newPackageLock)) {
            const origHash = crypto.hash("md5", fs.readFileSync(origPackageLock), "hex")
            const newHash = crypto.hash("md5", fs.readFileSync(newPackageLock), "hex")
            console.log("File md5 hashes:")
            console.log(`  ${origHash}: ${origPackageLock}`);
            console.log(`  ${newHash}: ${newPackageLock}`);
            if (origHash === newHash) {
                console.log("Success: The package-lock.json file does not require any changes.")
                return 0;
            }
            else {
                throw Error("Error! Please update the package-lock.json file.")
            }
        }
        else {
            throw Error("Couldn't recreate package-lock.json")
        }
    }
    finally {
        fs.rmSync(targetDir, {
            recursive: true,
        });
    }
}

checkPackageLock();

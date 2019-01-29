const Koa = require('koa');
const KoaRouter = require('koa-router');
const KoaCors = require('@koa/cors');
const fs = require('fs');
const path = require('path');
const moment = require('moment');

const PORT = 8320;
const HOST = 'localhost';
const DATA_DIRECTORY = path.join(__dirname, `../../core/data`);

const app = new Koa();
const router = new KoaRouter();

function readFile(path) {
    return new Promise((resolve, reject) => {
        fs.readFile(path, 'utf8', (error, data) => {
            if (error)
                return reject(error);

            return resolve(data);
        });
    });
}

/**
 * @param {*} path 
 * @returns Promise<string[]>
 */
function readDir(path) {
    return new Promise((resolve, reject) => {
        fs.readdir(path, 'utf8', (error, data) => {
            if (error)
                return reject(error);

            return resolve(data);
        });
    });
}

app.use(KoaCors({
    origin: '*'
}));

router.get('/daily', async (context) => {

    /** @type {string[]} */
    let fileNames = await readDir(DATA_DIRECTORY);

    fileNames = fileNames.filter((filename) => {
        return filename.match(/[0-9]{4}-[0-9]{2}-[0-9]{2}/gm);
    });

    fileNames = fileNames.sort((a, b) => {
        a = a.split('.')[0];
        b = b.split('.')[0];

        const dateA = moment(a, 'YYYY-MM-DD');
        const dateB = moment(b, 'YYYY-MM-DD');

        return dateA > dateB ? -1 : 1;  
    });

    const mostRecent = fileNames[0];

    const content = await readFile(path.join(DATA_DIRECTORY, mostRecent));
    context.body = content;
});

router.get('/last-race', async (context) => {
    try {
        const file = await readFile(path.join(DATA_DIRECTORY, `Last_Race`));
        context.body = file;
    } catch (error) {
        context.body = {};
    }
});

router.get('/championship', async (context) => {
    try {
        const file = await readFile(path.join(DATA_DIRECTORY, `Championship_${new Date().getFullYear()}.json`));
        context.body = file;    
    } catch (error) {
        context.body = {};   
    }
});

app
    .use(router.routes())
    .use(router.allowedMethods());

app.listen(PORT, HOST, () => console.log(`Listening on http://${HOST}:${PORT}`));

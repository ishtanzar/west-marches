console.log("WestMarches | Initialising");

import {WestMarchesLayer} from './controls.js';
import {registerSettings} from "./discord.js";
import {Kanka} from './kanka.js';

registerSettings();
WestMarchesLayer.initialize();
Kanka.initialize();

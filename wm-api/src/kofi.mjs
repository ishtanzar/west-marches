import {EmbedBuilder} from "discord.js";
import {readFileSync, writeFileSync} from "fs";
import dayjs from "dayjs";
import winston from "winston";

const logger = winston.createLogger({
    transports: [
        new winston.transports.Console({level: 'debug'})
    ]
});

export class KofiDonationProcessor {

    constructor(config, discord) {
        this.config = config;
        this.discord = discord;
    }

    async process_kofi_payload(data) {
        if(data.verification_token === this.config.kofi.verification_token) {
            logger.info('Ko-fi payload: {0}'.format(JSON.stringify(data)));

            /** @type {TextChannel} */
            const gm_channel = await this.fetchChannel(this.config.discord.gm_notif_channel);

            /** @type {TextChannel} */
            const progress_channel = await this.fetchChannel(this.config.discord.progress_channel);

            let cache = {}, progress_message;

            // noinspection JSCheckFunctionSignatures
            const gm_embed = new EmbedBuilder()
                .setColor(0x58b9ff)
                .setTitle("Nouveau don Ko-fi !")
                .addFields(
                    { name: "Nom", value: '```{0}```'.format(data.from_name || 'Anonyme'), inline: true},
                    { name: "Montant", value: '```{0} {1}```'.format(data.amount, data.currency), inline: true},
                    { name: "Message", value: data.message},
                )

            logger.debug('Notfying of new donation');
            await gm_channel.send({ embeds: [gm_embed] });

            try {
                cache = JSON.parse(readFileSync(this.config.cache.donations.path, 'utf-8'));
            } catch (e) {
                logger.warn('Cannot read cache file %s', this.config.cache.donations.path, { error: e })
            }

            cache.total = (cache.total || 0) + parseInt(data.amount);
            cache.donors = (cache.donors || 0) + 1;
            cache.monthly_fees = cache.monthly_fees || 30;

            // const image_url = new URL(req.protocol + "://" + req.hostname);
            // image_url.pathname = 'donations/progress.jpg';
            // image_url.searchParams.set("id", crypto.randomUUID());
            //
            // image_url.search = image_url.searchParams.toString()

            const player_embed = new EmbedBuilder()
                .setColor(0x58b9ff)
                .setTitle("Dons pour {0}".format(dayjs().format('MMMM YYYY')))
                .addFields(
                    { name: "Donateurs", value: '```{0}```'.format(cache.donors)},
                    { name: "Prise en charge des dépenses", value: '```{0} %```'.format(cache.total * 100 / cache.monthly_fees)},
                )
            //.setImage(image_url.toString())

            if(cache.message_id) {
                logger.debug('Updating message %s', cache.message_id)
                progress_message = await progress_channel.messages.fetch(cache.message_id)
                await progress_message.edit({ embeds: [player_embed] });
            } else {
                logger.debug('No message id in cache')
                progress_message = await progress_channel.send({ embeds: [player_embed] })
                cache.message_id = progress_message.id
            }

            try {
                writeFileSync(this.config.cache.donations.path, JSON.stringify(cache), 'utf-8')
            } catch (e) {
                logger.warn('Cannot rite cache file %s', this.config.cache.donations.path, { error: e });
                throw e;
            }

        } else {
            throw new Error('Invalid token');
        }
    }

    async fetchChannel(channel) {
        try {
            return await this.discord.channels.fetch(channel);
        } catch (e) {
            logger.warn('Cannot fetch discord channel {0}'.format(channel), { error: e});
        }
    }
}
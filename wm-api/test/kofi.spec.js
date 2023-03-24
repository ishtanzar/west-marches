import {app} from "../src/app.mjs";
import request from "supertest";
import {beforeEach, expect, jest, test} from '@jest/globals';
import BeeQueue from "bee-queue";
import redis from "redis-mock";
import {KofiDonationProcessor} from "../src/kofi.mjs";

describe("Test hook endpoint", () => {
    const hook_url = '/kofi/hook';

    test("It should handle no paylods", async () => {
        await request(app).post(hook_url).then(resp => {
            expect(resp.statusCode).toBe(400);
        });
    });

    test("It should handle invalid paylods", async () => {
        await request(app).post(hook_url).send({
            hello: 'world'
        }).then(resp => {
            expect(resp.statusCode).toBe(400);
        });

        await request(app).post(hook_url).send({
            data: 3
        }).then(resp => {
            expect(resp.statusCode).toBe(400);
        });
    });
});

describe('Test payload processing', () => {
    let uid = 0, queue, data, processor

    const discord_send = jest.fn(() => { return {id: 67890} });

    beforeEach(async () => {
        data = {
            "verification_token": process.env.KOFI_VERIFICATION,
            "message_id": "aa05fe61-671c-4d3c-913b-7c308f0287a9",
            "timestamp": "2023-03-21T08:47:57Z",
            "type": "Donation",
            "is_public": true,
            "from_name": "Jo Example",
            "message": "Good luck with the integration!",
            "amount": "3.00",
            "url": "https://ko-fi.com/Home/CoffeeShop?txid=00000000-1111-2222-3333-444444444444",
            "email": "jo.example@example.com",
            "currency": "USD",
            "is_subscription_payment": false,
            "is_first_subscription_payment": false,
            "kofi_transaction_id": "00000000-1111-2222-3333-444444444444",
            "shop_items": null,
            "tier_name": null,
            "shipping": null
        };

        processor = new KofiDonationProcessor({
            kofi: {
                verification_token: process.env.KOFI_VERIFICATION
            },
            discord: {
                gm_notif_channel: 12345,
                progress_channel: 54321
            },
            cache: {
                donations: {
                    path: '/tmp/cache.donations'
                }
            }
        }, {
            channels: {
                fetch: () => { return {send: discord_send}}
            }
        });

        queue = new BeeQueue(`test-${uid++}`, {
            redis: redis.createClient(),
            isWorker: false,
            getEvents: false,
            ensureScripts: false
        });

        await queue.ready();
    })

    test("It should fail on invalid payload", async () => {
        await expect(processor.process_kofi_payload({})).rejects.toThrow(Error);
    });

    test("It should fail on invalid token", async () => {
        data.verification_token = "xyz";

        await expect(processor.process_kofi_payload(data)).rejects.toThrow(Error);
    });
    test("It should work", async () => {
        await processor.process_kofi_payload(data)
    });
});
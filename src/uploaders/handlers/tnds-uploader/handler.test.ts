import AWS from 'aws-sdk';
import { S3Event } from 'aws-lambda';
import { s3TndsHandler } from './handler';
import * as mocks from './test-data/test-data';

jest.mock('aws-sdk');

describe('s3 handler with csv event', () => {
    const mockS3GetObject = jest.fn();
    const mockDynamoBatchWrite = jest.fn();
    const mockDynamoPut = jest.fn();

    beforeEach(() => {
        process.env.SERVICES_TABLE_NAME = 'TestServicesTable';
        process.env.TNDS_TABLE_NAME = 'TestTndsTable';

        (AWS.S3 as {}) = jest.fn().mockImplementation(() => {
            return {
                getObject: mockS3GetObject,
            };
        });

        mockS3GetObject.mockImplementation(() => ({
            promise(): Promise<{}> {
                return Promise.resolve({ Body: mocks.testCsv });
            },
        }));

        (AWS.DynamoDB.DocumentClient as {}) = jest.fn(() => {
            return { batchWrite: mockDynamoBatchWrite };
        });

        mockDynamoBatchWrite.mockImplementation(() => ({
            promise(): Promise<{}> {
                return Promise.resolve({});
            },
        }));
    });

    afterEach(() => {
        mockS3GetObject.mockReset();
        mockDynamoBatchWrite.mockReset();
        mockDynamoPut.mockReset();
    });

    it('sends the data to dynamo when a csv is created', async () => {
        const event: S3Event = mocks.mockS3Event('thisIsMyBucket', 'andThisIsTheNameOfTheThing.csv');

        await s3TndsHandler(event);

        expect(mockDynamoBatchWrite).toHaveBeenCalledTimes(1);
    });
});

describe('s3 handler with xml event', () => {
    const mockS3GetObject = jest.fn();
    const mockDynamoBatchWrite = jest.fn();
    const mockDynamoPut = jest.fn();

    beforeEach(() => {
        process.env.SERVICES_TABLE_NAME = 'TestServicesTable';
        process.env.TNDS_TABLE_NAME = 'TestTndsTable';

        (AWS.S3 as {}) = jest.fn().mockImplementation(() => {
            return {
                getObject: mockS3GetObject,
            };
        });

        mockS3GetObject.mockImplementation(() => ({
            promise(): Promise<{}> {
                return Promise.resolve({ Body: mocks.testXml });
            },
        }));

        (AWS.DynamoDB.DocumentClient as {}) = jest.fn(() => {
            return { put: mockDynamoPut };
        });

        mockDynamoPut.mockImplementation(() => ({
            promise(): Promise<{}> {
                return Promise.resolve({});
            },
        }));
    });

    afterEach(() => {
        mockS3GetObject.mockReset();
        mockDynamoBatchWrite.mockReset();
        mockDynamoPut.mockReset();
    });

    it('sends the data to dynamo when an xml is created', async () => {
        const event = mocks.mockS3Event('thisIsMyBucket', 'andThisIsTheNameOfTheThing.xml');

        await s3TndsHandler(event);

        expect(mockDynamoPut).toHaveBeenCalledTimes(2);
    });
});
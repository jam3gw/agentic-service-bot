export interface EnvironmentConfig {
    readonly environment: string;
    readonly domainName: string;
    readonly hostedZoneName: string;
    readonly subdomain: string;
}

export const environments: { [key: string]: EnvironmentConfig } = {
    dev: {
        environment: 'dev',
        domainName: 'agentic-service-bot.dev.jake-moses.com',
        hostedZoneName: 'jake-moses.com',
        subdomain: 'agentic-service-bot.dev'
    },
    prod: {
        environment: 'prod',
        domainName: 'agentic-service-bot.jake-moses.com',
        hostedZoneName: 'jake-moses.com',
        subdomain: 'agentic-service-bot'
    }
}; 
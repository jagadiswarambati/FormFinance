import createNextIntlPlugin from 'next-intl/plugin';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const currentDirectory = dirname(fileURLToPath(import.meta.url));
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');
const config = { reactStrictMode: true, outputFileTracingRoot: join(currentDirectory, '../..') };
export default withNextIntl(config);

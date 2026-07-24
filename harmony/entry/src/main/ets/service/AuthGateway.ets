import http from '@ohos.net.http';
import { AuthSession } from '../model/ReviewModels';

export class AuthGateway {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  }

  async login(username: string, password: string): Promise<AuthSession> {
    const client = http.createHttp();
    try {
      const form = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;
      const response = await client.request(`${this.baseUrl}/api/v1/auth/login`, {
        method: http.RequestMethod.POST,
        header: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        extraData: form,
        expectDataType: http.HttpDataType.STRING,
        connectTimeout: 8000,
        readTimeout: 12000
      });
      const text = response.result.toString();
      if (response.responseCode < 200 || response.responseCode >= 300) {
        throw new Error(`login failed (${response.responseCode}): ${text}`);
      }
      return JSON.parse(text) as AuthSession;
    } finally {
      client.destroy();
    }
  }
}

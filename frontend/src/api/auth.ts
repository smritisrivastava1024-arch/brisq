let memoryToken: string | null = null;

export const authStore = {
  setToken: (token: string) => {
    memoryToken = token;
  },
  getToken: () => memoryToken,
  clearToken: () => {
    memoryToken = null;
  }
};

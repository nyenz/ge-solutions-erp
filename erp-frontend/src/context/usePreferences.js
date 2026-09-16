// PATH: erp-frontend/src/context/usePreferences.js
import { useContext } from 'react';
import { PreferencesContext } from './PreferencesContext';

export const usePreferences = () => useContext(PreferencesContext);
export default usePreferences;

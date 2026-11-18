// The research theme. `astryx experimental theme editor` wrote this file once and never changes it again.
// The checked settings live in research.settings.json and the generated research.settings.ts;
// change them with `astryx experimental theme editor set research ...`. Add your own changes below: they win over the settings.
import {defineTheme} from '@astryxdesign/core/theme';
import {researchSettings} from './research.settings';

export const researchTheme = defineTheme({
  extends: researchSettings,
  name: 'research',
  // Retain readable Chinese body text on touch screens as well as desktops.
  adaptations: {rules: [{
    when: {width: {below: 'lg'}, pointer: 'coarse'},
    value: {tokens: {
      '--text-body-size': '1rem', '--text-body-leading': '1.75',
      '--text-supporting-size': '0.875rem', '--text-supporting-leading': '1.65',
      '--text-label-size': '1rem', '--text-label-leading': '1.5',
      '--text-heading-1-size': '1.75rem', '--text-heading-2-size': '1.5rem',
      '--text-heading-3-size': '1.25rem',
    }},
  }]},
});

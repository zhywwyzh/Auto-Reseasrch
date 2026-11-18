import React from 'react';
import {Token} from '@astryxdesign/core/Token';

const colors:Record<string,React.ComponentProps<typeof Token>['color']>={
  RUNNING:'blue',running:'blue',DISPATCHED:'blue',READY:'blue',
  COMPLETED:'green',completed:'green',succeeded:'green',passed:'green',accepted:'green',
  FAILED:'red',failed:'red',
  UNKNOWN:'orange',unknown:'orange',BLOCKED:'orange',blocked:'orange',
  NEEDS_RECONCILIATION:'orange',WAITING_EXTERNAL:'orange',REVISION_REQUIRED:'orange',
};
export function StatusPill({state,label}:{state?:string;label:string}){
  return <Token label={label} color={colors[state || ''] || 'gray'} size="md" />;
}

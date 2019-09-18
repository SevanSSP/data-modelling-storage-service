import React, { useEffect, useState } from 'react'
import { Datasource, DataSourceType, DmtApi } from '../../api/Api'
import axios from 'axios'
import { DocumentsState } from '../common/DocumentReducer'
import BlueprintPickerTree from './BlueprintPickerTree'
import { TreeNodeData } from '../../components/tree-view/Tree'

const api = new DmtApi()

type BlueprintPickerContentProps = {
  state: DocumentsState
  dispatch: any
  //the source treeNodeData that opened this picker.
  //@todo Document FinderWidget should pass its own document tree. Which dont use the SelectBlueprintNode
  sourceNode: TreeNodeData | undefined //undefined since DocumentFinderWidget uses this component.
}

export const BlueprintPickerContent = (props: BlueprintPickerContentProps) => {
  const { dispatch, state, sourceNode } = props
  const [blueprintDatasources, setBlueprintDatasources] = useState<
    Datasource[]
  >([])

  // fetch blueprints
  useEffect(() => {
    const url = api.dataSourcesGet(DataSourceType.Blueprints)
    axios
      .get(url)
      .then((res: any) => {
        const data: Datasource[] = res.data || []
        setBlueprintDatasources(data)
      })
      .catch((err: any) => {
        console.log(err)
      })
  }, [])
  return (
    <div>
      <BlueprintPickerTree
        datasources={blueprintDatasources}
        dispatch={dispatch}
        state={state}
        sourceNode={sourceNode}
      />
    </div>
  )
}

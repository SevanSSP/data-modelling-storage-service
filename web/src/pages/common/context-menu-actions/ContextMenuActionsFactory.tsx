//@ts-ignore
import { NotificationManager } from 'react-notifications'
import { createAction } from './actions/create'
import { updateAction } from './actions/update'
import { TreeNodeRenderProps } from '../../../components/tree-view/TreeNode'
import { SetShowModal } from './WithContextMenu'
import { deleteAction } from './actions/delete'
import { downloadAction } from './actions/download'
import { runnableAction } from './actions/runnable'

export enum ContextMenuActions {
  CREATE = 'CREATE',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  DOWNLOAD = 'DOWNLOAD',
  RUNNABLE = 'RUNNABLE',
}

export interface ContextMenuActionProps {
  node: TreeNodeRenderProps
  layout?: any
  setShowModal: SetShowModal
}

const getFormProperties = (action: any, props: ContextMenuActionProps) => {
  const { node, setShowModal, layout } = props

  const showError = (error: any) => {
    console.error(error)
    NotificationManager.error(error.response.data.message, 'Failed')
  }

  const [method, actionType] = action.type.split('/')

  switch (method) {
    case ContextMenuActions.CREATE: {
      return createAction(action, node, setShowModal, showError)
    }
    case ContextMenuActions.UPDATE: {
      return updateAction(action, node, setShowModal, showError)
    }
    case ContextMenuActions.DELETE: {
      return deleteAction(action, node, setShowModal, showError, layout)
    }
    case ContextMenuActions.DOWNLOAD: {
      return downloadAction(action)
    }
    case ContextMenuActions.RUNNABLE: {
      return runnableAction(action, node)
    }

    default:
      return {
        schemaUrl: '',
        dataUrl: '',
        onSubmit: () => {},
      }
  }
}

export class ContextMenuActionsFactory {
  getActionConfig(action: any, props: ContextMenuActionProps) {
    return {
      formProps: getFormProperties(action, props),
      action: action.type,
    }
  }
}

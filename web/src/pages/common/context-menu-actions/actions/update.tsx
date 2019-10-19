import Api2, { BASE_CRUD } from '../../../../api/Api2'
import { processFormData } from './utils/request'
import { TreeNodeRenderProps } from '../../../../components/tree-view/TreeNode'

const fetchUpdate = (action: any) => {
  return ({ onSuccess, onError = () => {} }: BASE_CRUD): void =>
    Api2.fetchWithTemplate({
      urlSchema: action.data.schemaUrl,
      urlData: action.data.dataUrl,
      onSuccess,
      onError,
    })
}

export const postUpdate = (setShowModal: Function) => {
  setShowModal(false)
}

export const updateAction = (
  action: any,
  node: TreeNodeRenderProps,
  setShowModal: Function,
  showError: Function
) => {
  return {
    fetchDocument: fetchUpdate(action),
    onSubmit: (formData: any) => {
      const data = processFormData(action.data.request, formData)
      Api2.put({
        data: data,
        url: action.data.url,
        onSuccess: (result: any) => {
          postUpdate(setShowModal)
        },
        onError: (error: any) => showError(error),
      })
    },
  }
}
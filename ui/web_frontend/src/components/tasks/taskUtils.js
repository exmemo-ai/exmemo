import axios from 'axios'
import { setDefaultAuthHeader, getURL } from '@/components/support/conn'

export const taskService = {
    async getRunningTasks(page = 1, pageSize = 10) {
        setDefaultAuthHeader()
        const response = await axios.get(getURL() + '/api/tasks/running_tasks/', {
            params: {
                page,
                page_size: pageSize
            }
        })
        return response.data
    },

    terminateTask: async (taskId) => {
        setDefaultAuthHeader()
        return await axios.post(getURL() + `/api/tasks/${taskId}/terminate/`)
    },

    deleteTask: async (taskId) => {
        setDefaultAuthHeader()
        return await axios.delete(getURL() + `/api/tasks/${taskId}/delete_task/`)
    },

    deleteAllCompletedTasks: async () => {
        setDefaultAuthHeader()
        return await axios.delete(getURL() + '/api/tasks/delete_completed_tasks/')
    }
}

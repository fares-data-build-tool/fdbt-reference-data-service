import '../design/Components.scss';
import React from 'react';

export interface TableFormProps {
    offset: number
}

class TableForm extends React.Component<TableFormProps> {

  private getRows(offset: number){
    const rows: any[] = [];
    for (let row = 1; row <= (10+offset); row++) {
        const cols: any[] = [];    
        for (let col = 1; col <= (10); col++) {
            cols.push(<td><input className="govuk-input" id={"row"+row+"col"+col} name={"row"+row+"col"+col} type="text"/></td>);
        }
        rows.push(<tr>{cols}</tr>);
    }
    return rows;
  }

  render () {
    const rows = this.getRows(this.props.offset);
    return (
    <form method='post' action='/api/stages' className="form-control ">
      <div className="govuk-form-group">
        <table className="govuk-table">
          <caption className="govuk-table__caption">Please fill out the table</caption>
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header">Header 1</th>
              <th scope="col" className="govuk-table__header">Header 2</th>
              <th scope="col" className="govuk-table__header">Header 3</th>
              <th scope="col" className="govuk-table__header">Header 4</th>
              <th scope="col" className="govuk-table__header">Header 5</th>
              <th scope="col" className="govuk-table__header">Header 6</th>
              <th scope="col" className="govuk-table__header">Header 7</th>
              <th scope="col" className="govuk-table__header">Header 8</th>
              <th scope="col" className="govuk-table__header">Header 9</th>
              <th scope="col" className="govuk-table__header">Header 10</th>
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {rows}
          </tbody>
        </table>
      </div>
      <input type="submit" value="Submit" className="govuk-button govuk-button--start" />
    </form>
    )
  }
}
export default TableForm
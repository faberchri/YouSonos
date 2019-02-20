import React from "react";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import TextField from '@material-ui/core/TextField';
import IconButton from '@material-ui/core/IconButton';

import CircularProgress from '@material-ui/core/CircularProgress';
import InputAdornment from '@material-ui/core/InputAdornment';

import Clear from '@material-ui/icons/Clear';

interface State {
}

const styles = (theme: Theme) => createStyles({
    textField: {
        minHeight: '50px',
        width: '100%',
        marginTop: '12px',
        marginBottom: '8px',
    }
});

interface Props extends WithStyles<typeof styles> {
    searchString: string,
    onValueChange: (searchString: string) => void,
    onFieldReset: () => void,
    indicateError: boolean,
    indicateSearchRunning: boolean
}

class SearchInputField extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
    }

    onChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        this.props.onValueChange(event.target.value);
    };

    render() {

        const {classes} = this.props;

        let textFieldAction;
        if (this.props.indicateSearchRunning) {
            textFieldAction =
                <CircularProgress size={30} />
        } else {
            if (this.props.searchString.length > 0) {
                textFieldAction =
                    <IconButton
                        aria-label="clear input"
                        onClick={this.props.onFieldReset}>
                        <Clear/>
                    </IconButton>
            }
        }

        let endAdornment;
        if (textFieldAction !== undefined) {
            endAdornment = {
                endAdornment: (
                    <InputAdornment position="end">
                        {textFieldAction}
                    </InputAdornment>
                ),
            };
        }

        return (
                <TextField
                    error={this.props.indicateError}
                    label="YouTube-URL"
                    className={classes.textField}
                    margin="dense"
                    variant="outlined"
                    onChange={this.onChange}
                    value={this.props.searchString}
                    InputProps={endAdornment}
                />
        );
    }
}

export default withStyles(styles)(SearchInputField);
